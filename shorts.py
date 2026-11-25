"""Shorts-Automatik: Twitch-Clips -> fertige YouTube Shorts (9:16, Untertitel, Überschrift).

Befehle:
  python shorts.py check                   zeigt die aktuellen Top-Clips pro Streamer
  python shorts.py scout                   lädt Kandidaten, transkribiert sie -> scout/<datum>.txt
  python shorts.py render picks.json       rendert ausgewählte Clips (mit Überschrift/Schnitt)
  python shorts.py run                     vollautomatisch: Top-Clips direkt rendern
"""

import argparse
import datetime as dt
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import tomllib
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "state.json"
SCOUT_DIR = ROOT / "scout"
FACE_MODEL = ROOT / "models" / "face_detection_yunet.onnx"
W, H = 1080, 1920
TOP_H = 700            # Standardhöhe der Facecam oben im Split-Layout
TOP_MIN, TOP_MAX = 620, 920  # Facecam-Fläche passt sich der Cam an (kein mittiger Beschnitt mehr)
BOT_H = H - TOP_H      # Höhe des Gameplays unten

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
warnings.filterwarnings("ignore", module="huggingface_hub")

# CUDA-Bibliotheken (pip: nvidia-cublas-cu12, nvidia-cudnn-cu12) für Whisper auf der GPU
for _d in glob.glob(str(ROOT / ".venv" / "Lib" / "site-packages" / "nvidia" / "*" / "bin")):
    os.add_dll_directory(_d)
    os.environ["PATH"] = _d + os.pathsep + os.environ["PATH"]


# ---------------------------------------------------------------- helpers

def load_config():
    return tomllib.loads((ROOT / "config.toml").read_text("utf-8-sig"))


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    pattern = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet",
                           "Packages", "Gyan.FFmpeg*", "*", "bin", "ffmpeg.exe")
    hits = glob.glob(pattern)
    if hits:
        return hits[0]
    sys.exit("ffmpeg nicht gefunden. Bitte installieren: winget install Gyan.FFmpeg")


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"{Path(cmd[0]).name} fehlgeschlagen:\n{r.stderr[-3000:]}")
    return r.stdout


def ytdlp(*args):
    return run([sys.executable, "-m", "yt_dlp", "--no-warnings", *args])


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text("utf-8-sig"))
    return {"done": {}}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), "utf-8")


def slug(text, n=40):
    s = re.sub(r"[^\w\-]+", "_", text, flags=re.UNICODE).strip("_")
    return (s or "clip")[:n]


def streamers(cfg, only=None, channel=None):
    return [s for s in cfg["streamer"]
            if (not only or s["name"].lower() == only.lower())
            and (not channel or s.get("channel", "kanal1") == channel)]


def chan(cfg, key):
    """Einstellungen eines YouTube-Kanals aus [channels.<key>] (mit Standardwerten)."""
    c = dict(cfg.get("channels", {}).get(key, {}))
    c.setdefault("key", key)
    c.setdefault("name", key)
    c.setdefault("language", cfg["general"].get("language", "de"))
    c.setdefault("hashtags", cfg["general"].get("hashtags", ["#shorts"]))
    c.setdefault("upload", "api")
    return c


def out_dir_for(cfg, channel_key):
    d = ROOT / cfg["general"].get("output_dir", "output") / channel_key / dt.date.today().isoformat()
    d.mkdir(parents=True, exist_ok=True)
    return d


def all_metas(cfg, channel_key=None):
    """Alle Short-Metadaten (.json neben den .mp4) – optional nur für einen Kanal."""
    res = []
    for m in sorted((ROOT / cfg["general"].get("output_dir", "output")).rglob("*.json")):
        meta = json.loads(m.read_text("utf-8-sig"))
        if "file" not in meta:
            continue
        if channel_key and meta.get("channel", "kanal1") != channel_key:
            continue
        res.append((m, meta))
    return res


def trim_args(start=None, end=None):
    a = []
    if start:
        a += ["-ss", f"{start:.2f}"]
    if end:
        a += ["-to", f"{end:.2f}"]
    return a


# ---------------------------------------------------------------- clips

def list_clips(channel, range_, limit):
    url = f"https://www.twitch.tv/{channel}/clips?filter=clips&range={range_}"
    data = json.loads(ytdlp("--flat-playlist", "-J", "--playlist-end", str(limit), url))
    clips = []
    for e in data.get("entries") or []:
        clips.append({
            "id": str(e.get("id")),
            "title": (e.get("title") or "").strip(),
            "views": e.get("view_count") or 0,
            "duration": e.get("duration") or 0,
            "url": e.get("url") or e.get("webpage_url"),
            "creator": e.get("uploader") or e.get("creator") or "",
        })
    clips.sort(key=lambda c: c["views"], reverse=True)
    return clips


def download_clip(url, dest_dir, fmt="best[height<=1080]/best"):
    dest_dir.mkdir(parents=True, exist_ok=True)
    for old in dest_dir.glob("source.*"):
        old.unlink()
    ytdlp("-f", fmt, "-o", str(dest_dir / "source.%(ext)s"), url)
    files = [p for p in dest_dir.glob("source.*") if p.suffix != ".part"]
    if not files:
        raise RuntimeError("Download fehlgeschlagen")
    return files[0]


# ---------------------------------------------------------------- transcription

_model = None


def transcribe(src, ffmpeg, cfg, start=None, end=None, language=None):
    """Gibt (segmente, wörter) zurück, jeweils (start, ende, text). GPU, sonst CPU."""
    import numpy as np
    global _model
    g = cfg["general"]
    pcm = subprocess.run([ffmpeg, "-v", "error", *trim_args(start, end), "-i", str(src), "-vn",
                          "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    if len(audio) < 16000:
        return [], []
    from faster_whisper import WhisperModel
    devices = ["cuda", "cpu"] if _model is None else [None]
    last = None
    for dev in devices:
        try:
            if dev:
                _model = WhisperModel(g.get("whisper_model", "medium"), device=dev,
                                      compute_type="float16" if dev == "cuda" else "int8")
            segs, _ = _model.transcribe(audio, language=language or g.get("language", "de"),
                                        word_timestamps=True, vad_filter=True)
            segs = list(segs)
            return ([(s.start, s.end, s.text.strip()) for s in segs],
                    [(w.start, w.end, w.word.strip()) for s in segs for w in (s.words or [])
                     if w.word.strip()])
        except Exception as e:
            last, _model = e, None
    raise RuntimeError(f"Transkription fehlgeschlagen: {last}")


# ---------------------------------------------------------------- layout

def detect_layout(src):
    """Sucht ein über den Clip stabiles Gesicht.
    klein -> Facecam über Gameplay ("split"), groß -> Kamera-Zuschnitt ("cam"), keins -> "blur"."""
    import cv2
    cap = cv2.VideoCapture(str(src))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    vw, vh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dw = 960
    dh = round(dw * vh / vw)
    det = cv2.FaceDetectorYN.create(str(FACE_MODEL), "", (dw, dh), 0.7)
    samples, valid, dets, grays = 14, 0, [], []
    for i in range(samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * (0.04 + 0.92 * i / (samples - 1))))
        ok, frame = cap.read()
        if not ok:
            continue
        valid += 1
        small = cv2.resize(frame, (dw, dh))
        grays.append(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
        _, faces = det.detect(small)
        for f in faces if faces is not None else []:
            x, y, w, h = (float(v) for v in f[:4])
            dets.append((i, (x + w / 2) / dw, (y + h / 2) / dh, w / dw, h / dh))
    cap.release()

    info = {"vw": vw, "vh": vh}
    best = []
    for d in dets:
        tol = max(0.05, d[3] * 0.8)
        members = [e for e in dets if abs(e[1] - d[1]) < tol and abs(e[2] - d[2]) < tol * 1.5
                   and 0.6 < e[4] / d[4] < 1.6]
        if len({e[0] for e in members}) > len({e[0] for e in best}):
            best = members
    if not valid or len({e[0] for e in best}) < max(3, 0.4 * valid):
        return {**info, "layout": "blur"}

    med = lambda k: sorted(e[k] for e in best)[len(best) // 2]
    ncx, ncy, nfw, nfh = med(1), med(2), med(3), med(4)
    # Großes Gesicht in der Bildmitte = Kamera füllt das Bild (Just Chatting / IRL)
    if nfh >= 0.14 and 0.28 < ncx < 0.72:
        return {**info, "layout": "cam", "cx": ncx * vw}

    # Sonst: Facecam über Gameplay. Rahmen der Facecam über Kanten suchen.
    cx, cy, fw, fh = ncx * vw, ncy * vh, nfw * vw, nfh * vh
    face_top = cy - fh / 2
    rect = find_facecam_rect(grays, ncx * dw, ncy * dh, nfw * dw, nfh * dh)
    if rect:
        x0, y0, x1, y1 = (v * vw / dw for v in rect)
    else:  # kein Rahmen (z.B. freigestellte Cam) -> Kopf + Schultern mit Luft nach oben
        cw = min(vw, fw * 3.6)
        ch = min(vh, cw * 0.75)
        x0 = min(max(cx - cw / 2, 0), vw - cw)
        y0 = min(max(face_top - fh * 0.9, 0), vh - ch)
        x1, y1 = x0 + cw, y0 + ch
    top_h, crop = fit_top(x0, y0, x1, y1, cx, face_top, fh)
    return {**info, "layout": "split", "facecam_border": bool(rect), "crop": crop, "top_h": top_h}


def fit_top(x0, y0, x1, y1, cx=None, face_top=None, fh=0.0):
    """Facecam-Ausschnitt passend zur oberen Fläche (Breite W, Höhe TOP_MIN..TOP_MAX).
    Die Höhe richtet sich nach der Facecam, statt alles auf eine feste Höhe zu zwingen.
    Zu hoch -> unten (Brust/Mikro) abschneiden, nie den Kopf. Zu breit -> seitlich ums Gesicht."""
    cw, ch = x1 - x0, y1 - y0
    top_h = int(min(max(W * ch / cw, TOP_MIN), TOP_MAX)) // 2 * 2
    a = W / top_h
    if cw / ch > a + 1e-3:
        nw = ch * a
        c = cx if cx is not None else x0 + cw / 2
        x0, cw = min(max(c - nw / 2, x0), x1 - nw), nw
    elif cw / ch < a - 1e-3:
        nh = cw / a
        t = face_top - 0.75 * fh if face_top is not None else y0 + (ch - nh) / 2
        t = min(max(t, y0), y1 - nh)
        face_cut = face_top is not None and face_top + 1.35 * fh > t + nh  # Kinn/Mund fiele weg
        if face_cut or (face_top is None and nh < ch * 0.9):
            # Ausschnitt würde das Gesicht anschneiden: ganze Cam zeigen, Seiten unscharf auffüllen
            return top_h, tuple(int(v) // 2 * 2 for v in (cw, ch, x0, y0)) + ("fit",)
        y0, ch = t, nh
    return top_h, tuple(int(v) // 2 * 2 for v in (cw, ch, x0, y0))


def find_facecam_rect(grays, cx, cy, fw, fh):
    """Sucht gerade Kanten (Facecam-Rahmen) um das Gesicht, gemittelt über mehrere Frames.
    Gibt (x0, y0, x1, y1) in Detektions-Pixeln zurück oder None."""
    import cv2
    import numpy as np
    gx = np.mean([np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)) for g in grays], axis=0)
    gy = np.mean([np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)) for g in grays], axis=0)
    h, w = grays[0].shape

    def edge(profile, lo, hi, frame_edge):
        lo, hi = int(max(lo, 0)), int(min(hi, len(profile)))
        if hi - lo < 3:
            return frame_edge
        seg = profile[lo:hi]
        i = int(np.argmax(seg))
        if seg[i] > 3.0 * (np.median(profile) + 1e-3):
            return lo + i
        # keine Kante gefunden, aber Bildrand in Reichweite -> Bildrand
        return frame_edge if (lo == 0 or hi == len(profile)) else None

    rows = slice(int(max(cy - fh, 0)), int(min(cy + fh, h)))
    cols = slice(int(max(cx - fw, 0)), int(min(cx + fw, w)))
    colp = gx[rows].mean(axis=0)
    rowp = gy[:, cols].mean(axis=1)
    left = edge(colp, cx - 5 * fw, cx - 1.0 * fw, 0)
    right = edge(colp, cx + 1.0 * fw, cx + 5 * fw, w)
    top = edge(rowp, cy - 4 * fh, cy - 1.0 * fh, 0)
    bottom = edge(rowp, cy + 1.0 * fh, cy + 5 * fh, h)
    if None in (left, right, top, bottom):
        return None
    rw, rh = right - left, bottom - top
    # Plausibilität: Rahmen deutlich größer als Gesicht, aber nicht das halbe Bild
    if not (1.8 * fw < rw < 0.6 * w and 1.6 * fh < rh < 0.8 * h):
        return None
    pad = 3  # Rahmenlinie selbst abschneiden
    return (left + pad, top + pad, right - pad, bottom - pad)


def build_filter(lay, streamer):
    """Gibt (filter_complex, überschrift_y, untertitel_y) zurück. Ausgang heißt [v]."""
    vw, vh = lay["vw"], lay["vh"]
    layout = lay["layout"]
    if "facecam" in streamer:  # manuelle Facecam aus config.toml hat Vorrang
        fx, fy, fw, fh = streamer["facecam"]
        layout = "split"
        top_h, crop = fit_top(vw * fx, vh * fy, vw * (fx + fw), vh * (fy + fh))
    elif layout == "split":
        crop, top_h = lay["crop"], lay.get("top_h", TOP_H)

    if layout == "split":
        cw, ch, cx, cy = crop[:4]
        bot_h = H - top_h
        # unteren Rand weglassen: dort sitzen oft eingebrannte Live-Untertitel des Streams
        gh = int(round(vh * (1 - float(streamer.get("cut_bottom", 0.13))) / 2) * 2)
        gw = min(vw, int(round(gh * W / bot_h / 2) * 2))
        if len(crop) > 4:  # "fit": ganze Cam, Seiten mit unscharfer Kopie füllen
            top = (f"[a]crop={cw}:{ch}:{cx}:{cy},split[ca][cb];"
                   f"[ca]scale={W}:{top_h}:force_original_aspect_ratio=increase,crop={W}:{top_h},"
                   f"boxblur=20:2,eq=brightness=-0.12[cbg];"
                   f"[cb]scale=-2:{top_h}[cfg];[cbg][cfg]overlay=(W-w)/2:0[top];")
        else:
            top = (f"[a]crop={cw}:{ch}:{cx}:{cy},scale={W}:{top_h}:force_original_aspect_ratio=increase,"
                   f"crop={W}:{top_h}[top];")
        f = (f"[0:v]split[a][b];" + top +
             f"[b]crop={gw}:{gh}:{(vw - gw) // 2}:0,scale={W}:{bot_h}[bot];"
             f"[top][bot]vstack,setsar=1[v]")
        return f, 135, top_h
    if layout == "cam":
        # unteren Rand weglassen (eingebrannte Live-Untertitel), Rest auf 9:16 zuschneiden
        ch = int(round(vh * (1 - float(streamer.get("cut_bottom", 0.11))) / 2) * 2)
        cw = int(round(ch * 9 / 16 / 2) * 2)
        x = int(min(max(lay["cx"] - cw / 2, 0), vw - cw))
        return f"[0:v]crop={cw}:{ch}:{x}:0,scale={W}:{H},setsar=1[v]", 300, 1400
    zoom = float(streamer.get("zoom", 1.3))
    f = (f"[0:v]split[a][b];"
         f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
         f"boxblur=25:2,eq=brightness=-0.15[bg];"
         f"[b]crop=iw/{zoom}:ih,scale={W}:-2[fg];"
         f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v]")
    fg_h = round(W / (16 / 9) * zoom)
    top = (H - fg_h) // 2
    return f, top // 2, top + fg_h + 170


# ---------------------------------------------------------------- subtitles

def group_words(words, max_words=3, max_chars=18, max_gap=0.6):
    chunks, cur = [], []
    for w in words:
        if cur:
            text = " ".join(x[2] for x in cur + [w])
            if len(cur) >= max_words or len(text) > max_chars or w[0] - cur[-1][1] > max_gap:
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return [(c[0][0], c[-1][1], " ".join(x[2] for x in c)) for c in chunks]


def ass_time(t):
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass_clean(text):
    return text.replace("\\", "").replace("{", "(").replace("}", ")")


FONT_DIR = ROOT / "fonts"
HIGHLIGHT = "#FFE500"   # aktuelles Wort in den Untertiteln


def ass_color(hex_rgb, alpha=0):
    """#RRGGBB -> ASS &HAABBGGRR"""
    h = hex_rgb.lstrip("#")
    return f"&H{alpha:02X}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def text_width(text, size, weight="Black"):
    try:
        from PIL import ImageFont
        return ImageFont.truetype(str(FONT_DIR / f"Montserrat-{weight}.ttf"), size).getlength(text)
    except Exception:
        return len(text) * size * 0.68


def wrap_px(text, size, max_w, weight="Black"):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if cur and text_width(test, size, weight) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def rounded_rect(w, h, r):
    """ASS-Zeichenpfad für ein abgerundetes Rechteck (w x h, Radius r)."""
    w, h, r = int(w), int(h), int(min(r, w / 2, h / 2))
    return (f"m {r} 0 l {w - r} 0 b {w} 0 {w} 0 {w} {r} l {w} {h - r} b {w} {h} {w} {h} {w - r} {h} "
            f"l {r} {h} b 0 {h} 0 {h} 0 {h - r} l 0 {r} b 0 0 0 0 {r} 0")


def chunk_words(words, max_words=3, max_chars=18, max_gap=0.6):
    """Gruppiert Wörter (start, ende, text) zu kurzen Untertitel-Blöcken."""
    chunks, cur = [], []
    for w in words:
        if cur:
            text = " ".join(x[2] for x in cur + [w])
            if len(cur) >= max_words or len(text) > max_chars or w[0] - cur[-1][1] > max_gap:
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def write_ass(path, word_chunks, sub_y, headline, head_y, duration, accent="#9146FF",
              tag="", divider_y=None, tag_y=None, head_dur=None):
    """Untertitel (Karaoke: aktuelles Wort gelb), Überschrift-Banner, Streamer-Schild,
    Trennbalken und Fortschrittsbalken."""
    white, black = "&H00FFFFFF", "&H00000000"
    acc = ass_color(accent)
    hl = ass_color(HIGHLIGHT)
    head = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Sub,Montserrat Black,88,{white},{white},{black},&H70000000,"
        "0,0,0,0,100,100,1,0,1,9,4,5,40,40,0,1\n"
        f"Style: Head,Montserrat Black,58,{white},{white},{black},&H00000000,"
        "0,0,0,0,100,100,0,0,1,0,0,5,40,40,0,1\n"
        f"Style: Tag,Montserrat ExtraBold,36,{white},{white},{black},&H00000000,"
        "0,0,0,0,100,100,1,0,1,0,0,5,40,40,0,1\n"
        f"Style: Box,Montserrat Black,10,{acc},{acc},{black},&H70000000,"
        "0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    T0, T1 = ass_time(0), ass_time(duration)
    pop = "\\fscx70\\fscy70\\t(0,180,\\fscx100\\fscy100)"
    ev = []

    # Trennbalken zwischen Facecam und Gameplay
    if divider_y is not None:
        ev.append(f"Dialogue: 0,{T0},{T1},Box,,0,0,0,,{{\\an7\\pos(0,{divider_y - 6})\\p1}}"
                  f"m 0 0 l 1080 0 l 1080 12 l 0 12{{\\p0}}")

    # Überschrift-Banner (abgerundet, Kanalfarbe) + Streamer-Schild
    if headline:
        size, pad_x, pad_y = 58, 34, 22
        lines = wrap_px(ass_clean(headline), size, 860)
        bw = max(text_width(l, size) for l in lines) + 2 * pad_x
        bh = len(lines) * size * 1.22 + 2 * pad_y
        # head_dur gesetzt -> Banner nur am Anfang, dann ausblenden (z.B. wenn es sonst ein Gesicht verdeckt)
        H1 = ass_time(min(head_dur, duration)) if head_dur else T1
        fade = "\\fad(0,350)" if head_dur else ""
        ev.append(f"Dialogue: 2,{T0},{H1},Box,,0,0,0,,{{\\an5\\pos(540,{head_y})\\p1\\shad8\\4a&H90&{pop}{fade}}}"
                  f"{rounded_rect(bw, bh, 28)}{{\\p0}}")
        ev.append(f"Dialogue: 3,{T0},{H1},Head,,0,0,0,,{{\\an5\\pos(540,{head_y}){pop}{fade}}}" + r"\N".join(lines))
        if tag:
            ty = int(tag_y if tag_y else head_y + bh / 2 + 42)
            tw = text_width(tag, 36, "ExtraBold") + 44
            ev.append(f"Dialogue: 2,{T0},{T1},Box,,0,0,0,,{{\\an5\\pos(540,{ty})\\p1\\1c&H000000&\\1a&H40&"
                      f"\\fad(300,0)}}{rounded_rect(tw, 60, 30)}{{\\p0}}")
            ev.append(f"Dialogue: 3,{T0},{T1},Tag,,0,0,0,,{{\\an5\\pos(540,{ty})\\fad(300,0)}}{ass_clean(tag)}")

    # Untertitel: Block springt rein, gesprochenes Wort leuchtet gelb
    for ci, chunk in enumerate(word_chunks):
        c_start = chunk[0][0]
        c_end = chunk[-1][1]
        nxt = word_chunks[ci + 1][0][0] if ci + 1 < len(word_chunks) else c_end + 0.4
        c_end = min(max(c_end, c_start + 0.3), nxt) if nxt > c_start else c_end
        texts = [ass_clean(w[2]).upper() for w in chunk]
        for wi, w in enumerate(chunk):
            s = c_start if wi == 0 else w[0]
            e = chunk[wi + 1][0] if wi + 1 < len(chunk) else c_end
            if e <= s:
                continue
            parts = [f"{{\\1c{hl}}}{t}{{\\1c{white}}}" if j == wi else t for j, t in enumerate(texts)]
            anim = "\\fscx80\\fscy80\\t(0,90,\\fscx100\\fscy100)" if wi == 0 else ""
            ev.append(f"Dialogue: 4,{ass_time(s)},{ass_time(e)},Sub,,0,0,0,,"
                      f"{{\\pos(540,{sub_y}){anim}}}" + " ".join(parts))

    # Fortschrittsbalken unten
    ev.append(f"Dialogue: 5,{T0},{T1},Box,,0,0,0,,{{\\an7\\pos(0,1906)\\p1\\fscx0"
              f"\\t(0,{int(duration * 1000)},\\fscx100)}}m 0 0 l 1080 0 l 1080 14 l 0 14{{\\p0}}")
    path.write_text(head + "\n".join(ev) + "\n", "utf-8")


def audio_peaks(src, ffmpeg, start=None, end=None, max_peaks=4, min_gap=3.0):
    """Zeitpunkte besonders lauter Momente (Schreien, Lachen) für Zoom-Effekte."""
    import numpy as np
    pcm = subprocess.run([ffmpeg, "-v", "error", *trim_args(start, end), "-i", str(src), "-vn",
                          "-ac", "1", "-ar", "8000", "-f", "f32le", "-"], capture_output=True).stdout
    a = np.frombuffer(pcm, dtype=np.float32)
    win = 800  # 0,1 s
    if len(a) < win * 30:
        return []
    rms = np.sqrt(np.convolve(a[: len(a) // win * win].reshape(-1, win).__pow__(2).mean(1),
                              np.ones(3) / 3, mode="same"))
    thr = rms.mean() + 1.6 * rms.std()
    order = np.argsort(rms)[::-1]
    peaks = []
    for i in order:
        t = i * 0.1
        if rms[i] < thr or len(peaks) >= max_peaks:
            break
        if t < 1.0 or any(abs(t - p) < min_gap for p in peaks):
            continue
        peaks.append(t)
    return sorted(peaks)


# ---------------------------------------------------------------- render

def probe_duration(src, ffmpeg):
    fp = str(Path(ffmpeg).with_name("ffprobe.exe"))
    return float(run([fp, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)]).strip())


def render_short(src, workdir, out_file, streamer, cfg, ffmpeg, headline="",
                 start=None, end=None, subtitles=True, language=None, accent="#9146FF"):
    lay = detect_layout(src)
    segs, words = transcribe(src, ffmpeg, cfg, start, end, language)
    vf, head_y, sub_y = build_filter(lay, streamer)
    vf = vf.replace("[0:v]", "[0:v]fps=30,", 1)
    full = probe_duration(src, ffmpeg)
    duration = min(end or full, full) - (start or 0)

    # Farben etwas kräftiger. Kein Zoom-Effekt mehr (Nutzerwunsch 25.11.: "der Zoom ist voll Arsch")
    post = "eq=saturation=1.12:contrast=1.04"
    split = lay["layout"] == "split" or "facecam" in streamer
    head_dur = None
    if split:
        # Facecam oben nicht verdecken: Banner unten übers Gameplay, nach 3 s ausblenden
        head_y, head_dur = sub_y + 330, 3.0  # sub_y = Höhe der Facecam-Fläche
    write_ass(workdir / "subs.ass", chunk_words(words) if subtitles else [], sub_y, headline, head_y,
              duration, accent, tag=f"twitch.tv/{streamer['twitch']}",
              divider_y=sub_y if split else None, tag_y=sub_y - 95 if split else None, head_dur=head_dur)
    # relativer Pfad -> keine Windows-Escape-Probleme
    vf = vf[:-3] + f"[v0];[v0]{post}[v1];[v1]ass=subs.ass:fontsdir=../../fonts[v]"
    run([ffmpeg, "-y", *trim_args(start, end), "-i", src.name, "-filter_complex", vf,
         "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", str(out_file.resolve())], cwd=workdir)
    return " ".join(s[2] for s in segs), lay["layout"]


def make_metadata(clip, streamer, transcript, cfg, title=None, channel=None):
    ch = channel or chan(cfg, streamer.get("channel", "kanal1"))
    tags = ch["hashtags"]
    en = ch["language"] == "en"
    name = streamer["name"]
    base = title or (clip["title"] if len(clip["title"]) > 3 else transcript[:60])
    full = base if name.lower() in base.lower() else f"{base} | {name}"
    if len(full) > 90:
        full = full[:87] + "..."
    full += " #shorts"
    desc = (f"{base}\n\n"
            f"🎥 Streamer: {name} – https://www.twitch.tv/{streamer['twitch']}\n"
            f"✂️ {'Original clip' if en else 'Original-Clip'}: {clip['url']}\n"
            + (f"{'Clipped by' if en else 'Clip erstellt von'}: {clip['creator']}\n" if clip.get("creator") else "")
            + ("\nAll rights to the content belong to the streamer.\n\n" if en
               else "\nAlle Rechte am Inhalt liegen beim Streamer.\n\n")
            + " ".join(tags + ["#" + re.sub(r"\W", "", name.lower())]))
    return {"title": full, "description": desc,
            "tags": [t.lstrip("#") for t in tags] + [name, streamer["twitch"]],
            "source": clip, "streamer": name, "transcript": transcript}


def produce(clip, s, cfg, ffmpeg, state, out_dir=None, pick=None):
    pick = pick or {}
    ch = chan(cfg, s.get("channel", "kanal1"))
    out_dir = out_dir or out_dir_for(cfg, ch["key"])
    label = pick.get("title") or clip["title"]
    prefix = "" if s["name"].lower() in label.lower() else slug(s["name"], 20) + "_"
    name = f"{prefix}{slug(label)}_{clip['id']}"
    work = ROOT / "work" / name
    out_file = out_dir / f"{name}.mp4"
    print(f"   -> {pick.get('headline') or clip['title']}")
    src = download_clip(clip["url"], work)
    transcript, layout = render_short(
        src, work, out_file, s, cfg, ffmpeg, headline=pick.get("headline", ""),
        start=pick.get("start"), end=pick.get("end"), subtitles=pick.get("subtitles", True),
        language=ch["language"], accent=ch.get("accent", "#9146FF"))
    meta = make_metadata(clip, s, transcript, cfg, pick.get("title"), ch)
    meta.update(file=str(out_file.relative_to(ROOT)), layout=layout, uploaded=False, channel=ch["key"])
    out_file.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), "utf-8")
    state["done"][clip["id"]] = {"file": meta["file"], "date": dt.date.today().isoformat()}
    save_state(state)
    shutil.rmtree(work, ignore_errors=True)
    print(f"      fertig ({layout}): {out_file.relative_to(ROOT)}")


# ---------------------------------------------------------------- commands

def cmd_check(cfg, args):
    g = cfg["general"]
    for s in streamers(cfg, args.streamer):
        clips = list_clips(s["twitch"], args.range or g["clip_range"], g.get("scan_limit", 30))
        print(f"\n== {s['name']} ({s['twitch']}): {len(clips)} Clips")
        for c in clips[:5]:
            print(f"   {c['views']:>7} Views  {c['duration']:>4.0f}s  {c['title']}")


def cmd_scout(cfg, args):
    """Lädt Kandidaten in niedriger Qualität, transkribiert sie, schreibt scout/<datum>.json/.txt"""
    g = cfg["general"]
    ffmpeg = find_ffmpeg()
    state = load_state()
    SCOUT_DIR.mkdir(exist_ok=True)
    out = SCOUT_DIR / f"{dt.date.today().isoformat()}.json"
    data = json.loads(out.read_text("utf-8-sig")) if out.exists() else []
    seen = {c["id"] for f in SCOUT_DIR.glob("*.json")  # Clips aus früheren Tagen nicht nochmal
            for c in json.loads(f.read_text("utf-8-sig"))}
    for s in streamers(cfg, args.streamer, args.channel):
        ch = chan(cfg, s.get("channel", "kanal1"))
        print(f"\n== {s['name']}  [{ch['name']}]")
        try:
            clips = list_clips(s["twitch"], args.range or g["clip_range"], g.get("scan_limit", 30))
        except Exception as e:
            print(f"   Clips konnten nicht geladen werden: {e}")
            continue
        cands = [c for c in clips if c["id"] not in state["done"] and c["id"] not in seen
                 and g.get("min_duration", 0) <= c["duration"] <= g.get("max_duration", 60)]
        for c in cands[:args.limit]:
            try:
                src = download_clip(c["url"], ROOT / "work" / "scout", "worst[height>=360]/worst")
                segs, words = transcribe(src, ffmpeg, cfg, language=ch["language"])
            except Exception as e:
                print(f"   FEHLER {c['title']}: {e}")
                continue
            c.update(streamer=s["name"], channel=ch["key"],
                     words_per_sec=round(len(words) / max(c["duration"], 1), 2),
                     segments=[[round(a, 1), round(b, 1), t] for a, b, t in segs])
            data.append(c)
            print(f"   {c['views']:>7}  {c['duration']:>3.0f}s  {len(words):>3} Wörter  {c['title']}")
            out.write_text(json.dumps(data, indent=1, ensure_ascii=False), "utf-8")
    shutil.rmtree(ROOT / "work" / "scout", ignore_errors=True)
    lines = []
    for key in sorted({c.get("channel", "kanal1") for c in data}):
        lines.append(f"########## KANAL: {chan(cfg, key)['name']} ({key}) ##########\n")
        for c in [c for c in data if c.get("channel", "kanal1") == key]:
            lines.append(f"### [{c['id']}] {c['streamer']} | \"{c['title']}\" | {c['views']} Views | "
                         f"{c['duration']:.0f}s | {c['words_per_sec']} Wörter/s")
            lines += [f"  {a:>5.1f}-{b:>5.1f}  {t}" for a, b, t in c["segments"]] or ["  (keine Sprache)"]
            lines.append("")
    out.with_suffix(".txt").write_text("\n".join(lines), "utf-8")
    print(f"\n{len(data)} Kandidaten -> {out.with_suffix('.txt').relative_to(ROOT)}")


def cmd_render(cfg, args):
    """Rendert eine Auswahl: picks.json = [{id, headline, title, start?, end?, subtitles?}]"""
    ffmpeg = find_ffmpeg()
    state = load_state()
    known = {}
    for f in sorted(SCOUT_DIR.glob("*.json")):
        for c in json.loads(f.read_text("utf-8-sig")):
            known[c["id"]] = c
    by_name = {s["name"]: s for s in cfg["streamer"]}
    for pick in json.loads(Path(args.picks).read_text("utf-8-sig")):
        clip = known.get(str(pick["id"]))
        if not clip:
            print(f"   unbekannte Clip-ID {pick['id']} (erst scout laufen lassen)")
            continue
        try:
            produce(clip, by_name[clip["streamer"]], cfg, ffmpeg, state, None, pick)
        except Exception as e:
            print(f"      FEHLER: {e}")


def cmd_run(cfg, args):
    g = cfg["general"]
    ffmpeg = find_ffmpeg()
    state = load_state()
    count = args.count or g.get("clips_per_streamer", 3)
    for s in streamers(cfg, args.streamer, args.channel):
        print(f"\n== {s['name']}")
        try:
            clips = list_clips(s["twitch"], args.range or g["clip_range"], g.get("scan_limit", 30))
        except Exception as e:
            print(f"   Clips konnten nicht geladen werden: {e}")
            continue
        todo = [c for c in clips if c["id"] not in state["done"]
                and g.get("min_duration", 0) <= c["duration"] <= g.get("max_duration", 60)][:count]
        for c in todo:
            try:
                headline = c["title"] if len(c["title"]) > 8 else ""
                produce(c, s, cfg, ffmpeg, state, None, {"headline": headline})
            except Exception as e:
                print(f"      FEHLER: {e}")


# ---------------------------------------------------------------- youtube

YT_SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
             "https://www.googleapis.com/auth/youtube.readonly"]


YT_MANAGE_SCOPES = ["https://www.googleapis.com/auth/youtube"]  # Kanal/Videos bearbeiten


def youtube_client(channel, scopes=None, token_suffix=""):
    """Verbindet sich mit dem YouTube-Kanal. Beim ersten Mal öffnet sich der Browser zur Anmeldung.
    Für Verwaltung (Kanal bearbeiten) eigener Login mit token_suffix="_manage"."""
    scopes = scopes or YT_SCOPES
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    secret = ROOT / "client_secret.json"
    if not secret.exists():
        sys.exit("client_secret.json fehlt. Anleitung: YOUTUBE_SETUP.md")
    tok = ROOT / "tokens" / f"{channel}{token_suffix}.json"
    creds = Credentials.from_authorized_user_file(str(tok), scopes) if tok.exists() else None
    if creds and not creds.has_scopes(scopes):
        creds = None
    if creds and not creds.valid and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None
    if not creds or not creds.valid:
        print(f"Browser öffnet sich: Mit dem Google-Konto anmelden und den Kanal für '{channel}' auswählen.")
        flow = InstalledAppFlow.from_client_secrets_file(str(secret), scopes)
        creds = flow.run_local_server(port=0, prompt="consent")
    tok.parent.mkdir(exist_ok=True)
    tok.write_text(creds.to_json(), "utf-8")
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def channel_name(yt):
    items = yt.channels().list(part="snippet", mine=True).execute().get("items", [])
    return items[0]["snippet"]["title"] if items else "(kein Kanal gefunden)"


def next_slots(times, taken, n):
    """Nächste freie Veröffentlichungszeiten (lokal) aus den Tageszeiten in config.toml."""
    now = dt.datetime.now().astimezone()
    taken = set(taken)
    slots, day = [], now.date()
    while len(slots) < n and times:
        for t in sorted(times):
            hh, mm = map(int, t.split(":"))
            slot = dt.datetime.combine(day, dt.time(hh, mm)).astimezone()
            iso = slot.isoformat(timespec="seconds")
            if slot > now + dt.timedelta(minutes=30) and iso not in taken:
                slots.append(iso)
                if len(slots) == n:
                    break
        day += dt.timedelta(days=1)
    return slots


def cmd_auth(cfg, args):
    channel = args.channel or cfg.get("youtube", {}).get("channel", "kanal1")
    yt = youtube_client(channel)
    print(f"Verbunden: '{channel}' -> YouTube-Kanal \"{channel_name(yt)}\"")


def cmd_upload(cfg, args):
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    yc = cfg.get("youtube", {})
    channel = args.channel or yc.get("channel", "kanal1")
    ch = chan(cfg, channel)
    if ch["upload"] != "api":
        sys.exit(f"Kanal '{channel}' lädt über den Browser hoch (shorts.py browser-queue --channel {channel}).")
    todo = []
    for m, meta in all_metas(cfg, channel):
        if args.only and args.only.lower() not in m.stem.lower():
            continue
        if not meta.get("uploaded") and not meta.get("skip") and (ROOT / meta["file"]).exists():
            todo.append((m, meta))
    limit = args.limit or yc.get("uploads_per_run", 3)
    todo = todo[:limit]
    if not todo:
        print("Nichts hochzuladen.")
        return

    yt = youtube_client(channel)
    print(f"Kanal: {channel_name(yt)}  |  {len(todo)} Video(s)")
    state = load_state()
    taken = state.setdefault("scheduled" if channel == "kanal1" else f"scheduled_{channel}", [])
    privacy = args.privacy or yc.get("privacy", "private")
    slots = next_slots(yc.get("publish_times", []), taken, len(todo)) if args.schedule else []

    for i, (m, meta) in enumerate(todo):
        publish_at = slots[i] if i < len(slots) else None
        clean = lambda s: s.replace("<", "").replace(">", "")
        tags, total = [], 0
        for t in meta.get("tags", []):
            if total + len(t) + 3 > 450:
                break
            tags.append(t)
            total += len(t) + 3
        body = {
            "snippet": {"title": clean(meta["title"])[:100], "description": clean(meta["description"])[:4900],
                        "tags": tags, "categoryId": str(yc.get("category_id", "20")),
                        "defaultLanguage": ch["language"], "defaultAudioLanguage": ch["language"]},
            "status": {"privacyStatus": "private" if publish_at else privacy,
                       "selfDeclaredMadeForKids": False},
        }
        if publish_at:
            body["status"]["publishAt"] = publish_at
        print(f"   -> {meta['title']}" + (f"  (geplant: {publish_at})" if publish_at else f"  ({privacy})"))
        try:
            req = yt.videos().insert(part="snippet,status", body=body,
                                     media_body=MediaFileUpload(str(ROOT / meta["file"]),
                                                                chunksize=-1, resumable=True))
            resp = None
            while resp is None:
                _, resp = req.next_chunk()
        except HttpError as e:
            msg = str(e)
            print(f"      FEHLER: {msg[:400]}")
            if "quotaExceeded" in msg or "uploadLimitExceeded" in msg:
                print("      Tageslimit erreicht – morgen geht es weiter.")
                break
            continue
        meta.update(uploaded=True, youtube_id=resp["id"], channel=channel,
                    uploaded_at=dt.datetime.now().isoformat(timespec="seconds"),
                    publish_at=publish_at, privacy=resp.get("status", {}).get("privacyStatus"))
        m.write_text(json.dumps(meta, indent=2, ensure_ascii=False), "utf-8")
        if publish_at:
            taken.append(publish_at)
            save_state(state)
        print(f"      hochgeladen: https://youtube.com/shorts/{resp['id']}")


# ---------------------------------------------------------------- browser-upload

BROWSER_LIMIT = 9.5 * 1024 * 1024   # Claude in Chrome lädt max. 10 MB pro Datei hoch


def small_version(src, ffmpeg):
    """Kopie unter 9,5 MB (HEVC 2-Pass) für Browser-Uploads; kleine Dateien werden nur kopiert."""
    dst = src.parent / "klein" / src.name
    if dst.exists():
        return dst
    dst.parent.mkdir(exist_ok=True)
    if src.stat().st_size <= BROWSER_LIMIT:
        shutil.copy2(src, dst)
        return dst
    fp = str(Path(ffmpeg).with_name("ffprobe.exe"))
    dur = float(run([fp, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)]).strip())
    vkbit = int(BROWSER_LIMIT * 8 / 1000 * 0.95 / dur - 128)
    common = ["-c:v", "libx265", "-preset", "medium", "-b:v", f"{vkbit}k", "-tag:v", "hvc1", "-pix_fmt", "yuv420p"]
    work = dst.parent
    run([ffmpeg, "-y", "-i", str(src), *common, "-x265-params", "pass=1:stats=x265pass:log-level=error",
         "-an", "-f", "null", "NUL"], cwd=work)
    run([ffmpeg, "-y", "-i", str(src), *common, "-x265-params", "pass=2:stats=x265pass:log-level=error",
         "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(dst)], cwd=work)
    for p in work.glob("x265pass*"):
        p.unlink()
    return dst


def cmd_browser_queue(cfg, args):
    """Bereitet Browser-Uploads vor: kleine Dateien + queue/<kanal>.json mit Titel/Beschreibung."""
    ffmpeg = find_ffmpeg()
    ch = chan(cfg, args.channel)
    todo = [(m, meta) for m, meta in all_metas(cfg, args.channel)
            if not meta.get("uploaded") and not meta.get("skip") and (ROOT / meta["file"]).exists()]
    todo = todo[:args.limit or cfg.get("youtube", {}).get("uploads_per_run", 6)]
    queue = []
    for m, meta in todo:
        small = small_version(ROOT / meta["file"], ffmpeg)
        queue.append({"meta": str(m), "file": str(small), "size_mb": round(small.stat().st_size / 1e6, 1),
                      "title": meta["title"][:100], "description": meta["description"][:4900]})
    qdir = ROOT / "queue"
    qdir.mkdir(exist_ok=True)
    out = qdir / f"{args.channel}.json"
    out.write_text(json.dumps({"channel": ch, "videos": queue}, indent=2, ensure_ascii=False), "utf-8")
    print(f"{len(queue)} Video(s) für '{ch['name']}' bereit -> {out.relative_to(ROOT)}")
    for q in queue:
        print(f"   {q['size_mb']:>4} MB  {q['title']}")


def cmd_mark_uploaded(cfg, args):
    m = Path(args.meta)
    meta = json.loads(m.read_text("utf-8-sig"))
    meta.update(uploaded=True, youtube_id=args.youtube_id, upload_method="youtube_studio",
                uploaded_at=dt.datetime.now().isoformat(timespec="seconds"), privacy=args.privacy)
    m.write_text(json.dumps(meta, indent=2, ensure_ascii=False), "utf-8")
    print(f"markiert: {meta['title']} -> https://youtube.com/shorts/{args.youtube_id}")


def read_client(channel):
    """Nur-Lesen (öffentliche Zahlen): Kanäle ohne eigene API-Verbindung (Browser-Upload) lesen über kanal1,
    damit sich nie ein Login-Fenster öffnet."""
    return youtube_client(channel if (ROOT / "tokens" / f"{channel}.json").exists() else "kanal1")


def cmd_status(cfg, args):
    """Zeigt Sichtbarkeit und Verarbeitungsstatus von Videos (kostet 1 Quota-Einheit)."""
    yt = read_client(args.channel)
    r = yt.videos().list(part="status,snippet", id=",".join(args.ids)).execute()
    found = set()
    for it in r.get("items", []):
        s = it["status"]
        found.add(it["id"])
        print(it["id"], s["privacyStatus"], s["uploadStatus"], s.get("rejectionReason", ""),
              it["snippet"]["title"])
    for i in set(args.ids) - found:
        print(i, "NICHT GEFUNDEN")


def _headlines():
    res = {}
    for f in sorted((ROOT / "picks").glob("*.json")):
        try:
            for p in json.loads(f.read_text("utf-8-sig")):
                res[str(p["id"])] = p
        except Exception:
            pass
    return res


def cmd_stats(cfg, args):
    """Holt Aufrufe/Likes/Kommentare aller geposteten Shorts, speichert Verlauf in stats/<kanal>.json"""
    picks = _headlines()
    metas = [(m, meta) for m, meta in all_metas(cfg, args.channel) if meta.get("youtube_id")]
    if not metas:
        print("Noch nichts gepostet.")
        return
    yt = read_client(args.channel)
    items = {}
    ids = [meta["youtube_id"] for _, meta in metas]
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="statistics,status", id=",".join(ids[i:i + 50])).execute()
        items.update({it["id"]: it for it in r.get("items", [])})
    sdir = ROOT / "stats"
    sdir.mkdir(exist_ok=True)
    sfile = sdir / f"{args.channel}.json"
    hist = json.loads(sfile.read_text("utf-8-sig")) if sfile.exists() else {}
    now = dt.datetime.now()
    ffmpeg = find_ffmpeg()
    fp = str(Path(ffmpeg).with_name("ffprobe.exe"))
    rows = []
    for m, meta in metas:
        vid = meta["youtube_id"]
        it = items.get(vid)
        if not it or it["status"]["privacyStatus"] != "public":
            continue
        st = it["statistics"]
        views, likes, comments = (int(st.get(k, 0)) for k in ("viewCount", "likeCount", "commentCount"))
        up = dt.datetime.fromisoformat(meta.get("uploaded_at", now.isoformat()))
        age_h = max((now - up).total_seconds() / 3600, 0.1)
        sid = str(meta.get("source", {}).get("id", ""))
        pick = picks.get(sid, {})
        e = hist.setdefault(vid, {})
        if "dur" not in e:
            try:
                e["dur"] = round(float(run([fp, "-v", "error", "-show_entries", "format=duration",
                                            "-of", "csv=p=0", str(ROOT / meta["file"])]).strip()), 1)
            except Exception:
                e["dur"] = None
        e.update(title=meta["title"], streamer=meta.get("streamer"), headline=pick.get("headline"),
                 experiment=pick.get("experiment"), clip_title=meta.get("source", {}).get("title"),
                 design="v2" if "kanal" in meta["file"] else "v1",
                 layout=meta.get("layout"), uploaded_at=meta.get("uploaded_at"),
                 upload_hour=up.hour, perf=meta.get("perf", {}))
        e.setdefault("snapshots", []).append(
            {"t": now.isoformat(timespec="minutes"), "age_h": round(age_h, 1),
             "views": views, "likes": likes, "comments": comments})
        e.update(views=views, likes=likes, comments=comments, age_h=round(age_h, 1),
                 views_per_h=round(views / age_h, 1),
                 like_rate=round(likes / views * 100, 1) if views else 0.0)
        rows.append((vid, e))
    sfile.write_text(json.dumps(hist, indent=1, ensure_ascii=False), "utf-8")
    rows.sort(key=lambda r: r[1]["views"], reverse=True)
    print(f"{'Aufrufe':>8} {'/Std':>6} {'Likes%':>6} {'Alter':>6} {'Länge':>5}  {'Streamer':<13} ID           Titel  [perf]")
    for vid, e in rows:
        perf = " ".join(f"{k}={v}" for k, v in e["perf"].items() if k != "checked_at")
        print(f"{e['views']:>8} {e['views_per_h']:>6} {e['like_rate']:>6} {e['age_h']:>5}h {str(e['dur']):>5}  "
              f"{(e['streamer'] or '')[:13]:<13} {vid}  {e['title'][:60]}" + (f"  [{perf}]" if perf else ""))
    print(f"\n{len(rows)} öffentliche Shorts -> {sfile.relative_to(ROOT)}")


def cmd_perf(cfg, args):
    """Trägt Werte aus YouTube Studio ein, z.B. perf <id> angesehen=62 avd=14.5 (Prozent/Sekunden)"""
    for m, meta in all_metas(cfg):
        if meta.get("youtube_id") == args.youtube_id:
            perf = meta.setdefault("perf", {})
            for kv in args.values:
                k, _, v = kv.partition("=")
                try:
                    v = float(v.replace(",", ".").rstrip("%s"))
                except ValueError:
                    pass
                perf[k] = v
            perf["checked_at"] = dt.datetime.now().isoformat(timespec="minutes")
            m.write_text(json.dumps(meta, indent=2, ensure_ascii=False), "utf-8")
            print(f"{meta['title']}: {perf}")
            return
    print("Video-ID nicht gefunden:", args.youtube_id)


def cmd_contact_sheet(cfg, args):
    """Standbilder eines Shorts (Spalten = Zeitpunkte) zum Prüfen -> <video>_sheet.png"""
    ffmpeg = find_ffmpeg()
    src = Path(args.video)
    fp = str(Path(ffmpeg).with_name("ffprobe.exe"))
    dur = float(run([fp, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)]).strip())
    times = [0.8, 2.5] + [dur * k / 5 for k in range(1, 5)] + [max(dur - 1.0, 0)]
    out = src.with_name(src.stem + "_sheet.png")
    ins, chains = [], []
    for k, t in enumerate(times):
        ins += ["-ss", f"{t:.2f}", "-i", str(src)]
        chains.append(f"[{k}:v]trim=end_frame=1,scale=270:480,setsar=1[t{k}]")
    filt = ";".join(chains) + ";" + "".join(f"[t{k}]" for k in range(len(times))) + \
        f"hstack=inputs={len(times)}[o]"
    run([ffmpeg, "-v", "error", "-y", *ins, "-filter_complex", filt, "-map", "[o]", "-frames:v", "1", str(out)])
    print(out, "Zeitpunkte:", ", ".join(f"{t:.1f}s" for t in times), f"(Länge {dur:.1f}s)")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    p = argparse.ArgumentParser(description="Twitch-Clips -> YouTube Shorts")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "scout", "run"):
        sp = sub.add_parser(name)
        sp.add_argument("--streamer", help="nur diesen Streamer (Name aus config.toml)")
        sp.add_argument("--range", help="24hr, 7d, 30d oder all")
        sp.add_argument("--channel", help="nur Streamer dieses Kanals (z.B. kanal2)")
        if name == "scout":
            sp.add_argument("--limit", type=int, default=10, help="Kandidaten pro Streamer")
        if name == "run":
            sp.add_argument("--count", type=int, help="Shorts pro Streamer")
    sp = sub.add_parser("render")
    sp.add_argument("picks", help="JSON-Datei mit der Auswahl")
    sp = sub.add_parser("auth", help="YouTube-Kanal verbinden")
    sp.add_argument("--channel", help="Name des Kanals (frei wählbar, z.B. kanal1)")
    sp = sub.add_parser("upload", help="fertige Shorts hochladen")
    sp.add_argument("--channel", help="Name des Kanals (wie bei auth)")
    sp.add_argument("--limit", type=int, help="max. Anzahl Videos")
    sp.add_argument("--privacy", choices=["private", "unlisted", "public"])
    sp.add_argument("--only", help="nur Videos, deren Dateiname diesen Text enthält (z.B. Clip-ID)")
    sp.add_argument("--schedule", action="store_true",
                    help="auf die publish_times aus config.toml verteilen")
    sp = sub.add_parser("browser-queue", help="Browser-Uploads vorbereiten (kleine Dateien + Liste)")
    sp.add_argument("--channel", required=True)
    sp.add_argument("--limit", type=int)
    sp = sub.add_parser("mark-uploaded", help="Browser-Upload als erledigt eintragen")
    sp.add_argument("meta", help="Pfad zur .json des Shorts")
    sp.add_argument("youtube_id")
    sp.add_argument("--privacy", default="public")
    sp = sub.add_parser("status", help="Sichtbarkeit von Videos prüfen")
    sp.add_argument("ids", nargs="+")
    sp.add_argument("--channel", default="kanal1")
    sp = sub.add_parser("sheet", help="Standbilder eines Shorts zum Prüfen")
    sp.add_argument("video")
    sp = sub.add_parser("stats", help="Performance aller geposteten Shorts abrufen")
    sp.add_argument("--channel", default="kanal1")
    sp = sub.add_parser("perf", help="Studio-Werte (Angesehen %%, Wiedergabedauer) eintragen")
    sp.add_argument("youtube_id")
    sp.add_argument("values", nargs="+", help="z.B. angesehen=62 avd=14.5")
    args = p.parse_args()
    cfg = load_config()
    {"check": cmd_check, "scout": cmd_scout, "render": cmd_render, "run": cmd_run,
     "auth": cmd_auth, "upload": cmd_upload, "browser-queue": cmd_browser_queue,
     "mark-uploaded": cmd_mark_uploaded, "status": cmd_status,
     "sheet": cmd_contact_sheet, "stats": cmd_stats, "perf": cmd_perf}[args.cmd.replace("_", "-")](cfg, args)


if __name__ == "__main__":
    main()
