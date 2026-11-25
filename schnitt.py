"""Pro-Schnitt für Shorts – wird von shorts.py vor dem Rendern aufgerufen.

Was passiert (alles im Pick steuerbar):
  * Jump-Cuts: tote Pausen (keine Sprache UND leise, länger als ~0,9 s) werden herausgeschnitten,
    Lacher/Schreie/laute Momente bleiben drin.                        -> "tighten": false schaltet ab
  * Mehrfach-Schnitt: nur die guten Teile eines Gesprächs aneinander. -> "segments": [[s, e], [s, e], ...]
    (ersetzt start/end; Zeiten in Sekunden im Original-Clip)
  * Geschützte Stellen: nie kürzen (z. B. stiller Aufbau vor der Pointe). -> "keep": [[s, e], ...]
  * Cold Open: die stärkste Sekunde (Pointe/Reaktion) ganz vorne als Teaser, danach normal.
                                                                      -> "hook": [s, e]  (1–2,5 s)
Kein Zoom (Nutzer-Vorgabe). Schnitte sind harte Cuts mit 15 ms Audio-Blende gegen Knackser.
"""
import subprocess
from pathlib import Path

MIN_GAP = 0.9      # Pausen ab dieser Länge werden gekürzt
PAD = 0.18         # so viel Pause bleibt vor/nach jedem Schnitt stehen
WORD_PAD = 0.12    # Puffer um jedes gesprochene Wort
TAIL_PROTECT = 1.2  # das Ende eines Segments (Reaktion/Pointe) nie kürzen
WIN = 0.05
MAX_CUT_SHARE = 0.25  # höchstens ein Viertel eines Segments wird weggeschnitten


def _rms_db(src, ffmpeg, a, b):
    import numpy as np
    pcm = subprocess.run([ffmpeg, "-v", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(src), "-vn",
                          "-ac", "1", "-ar", "8000", "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(pcm, dtype=np.float32)
    n = int(8000 * WIN)
    if len(x) < n * 4:
        return np.array([])
    x = x[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((x ** 2).mean(1)) + 1e-6)


def _motion(src, a, b, t):
    """Bildbewegung je Zeitfenster t (mittlere Pixeländerung, kleine Graustufen-Frames)."""
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(str(src))
    cap.set(cv2.CAP_PROP_POS_MSEC, a * 1000)
    times, vals, prev = [], [], None
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        ts = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if ts > b:
            break
        g = cv2.cvtColor(cv2.resize(fr, (160, 90)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            times.append(ts)
            vals.append(float(np.abs(g - prev).mean()))
        prev = g
    cap.release()
    if not times:
        return np.zeros(len(t))
    times, vals = np.array(times), np.array(vals)
    # pro Fenster das Maximum in ±0,15 s (kurze Bewegungen zählen)
    return np.array([vals[(times >= x - .15) & (times <= x + .15)].max(initial=0) for x in t])


def _dead_spans(src, ffmpeg, cfg, a, b, language, transcribe, keep):
    """Zeitspannen (absolut) innerhalb [a, b], die rausfliegen dürfen:
    keine Sprache UND leise UND kaum Bewegung im Bild – also Stellen, an denen wirklich nichts passiert."""
    import numpy as np
    _, words = transcribe(src, ffmpeg, cfg, a, b, language)
    db = _rms_db(src, ffmpeg, a, b)
    if not len(db):
        return []
    thr = np.percentile(db, 60)  # „laut“ = lauter als 60 % des Clips (Lachen, Schreien, Action)
    t = a + np.arange(len(db)) * WIN
    mot = _motion(src, a, b, t)
    still = mot < np.percentile(mot, 55)  # ruhiger als der Großteil des Clips
    speech = np.zeros(len(db), bool)
    for w0, w1, _ in words:
        speech |= (t >= a + w0 - WORD_PAD) & (t <= a + w1 + WORD_PAD)
    protected = t >= b - TAIL_PROTECT
    for k0, k1 in keep:
        protected |= (t >= k0) & (t <= k1)
    dead = ~speech & (db < thr) & still & ~protected
    spans, i = [], 0
    while i < len(dead):
        if dead[i]:
            j = i
            while j < len(dead) and dead[j]:
                j += 1
            s0, s1 = t[i], t[j - 1] + WIN
            if s1 - s0 >= MIN_GAP:
                lead = 0.05 if abs(s0 - a) < 1e-6 else PAD  # Leerlauf ganz am Anfang komplett weg
                spans.append((s0 + lead, s1 - PAD))
            i = j
        else:
            i += 1
    spans = [(x, y) for x, y in spans if y - x > 0.25]
    # Tempo straffen, aber nicht zerhacken: höchstens MAX_CUT_SHARE des Segments, längste Pausen zuerst
    budget, chosen = MAX_CUT_SHARE * (b - a), []
    for x, y in sorted(spans, key=lambda s: s[0] - s[1]):
        if y - x <= budget:
            chosen.append((x, y))
            budget -= y - x
    return sorted(chosen)


def plan(src, ffmpeg, cfg, pick, dur, language, transcribe):
    base = pick.get("segments") or [[pick.get("start") or 0.0, pick.get("end") or dur]]
    base = [(max(0.0, float(s)), min(dur, float(e))) for s, e in base if float(e) > float(s)]
    keep = [tuple(map(float, k)) for k in pick.get("keep", [])]
    segs, removed = [], 0.0
    for a, b in base:
        cuts = _dead_spans(src, ffmpeg, cfg, a, b, language, transcribe, keep) if pick.get("tighten", True) else []
        cur = a
        for c0, c1 in cuts:
            if c0 > cur:
                segs.append((cur, c0))
            removed += c1 - max(c0, cur)
            cur = max(cur, c1)
        if b > cur:
            segs.append((cur, b))
    segs = [(x, y) for x, y in segs if y - x >= 0.3]
    hook = pick.get("hook")
    if hook:
        segs.insert(0, (float(hook[0]), float(hook[1])))
    info = {"segmente": len(segs), "pausen_raus_s": round(float(removed), 1), "cold_open": bool(hook),
            "mehrfach": bool(pick.get("segments")),
            "laenge_s": round(float(sum(y - x for x, y in segs)), 1)}
    segs = [(float(x), float(y)) for x, y in segs]
    return segs, info


def render(src, ffmpeg, segs, out):
    parts, labels = [], []
    for i, (a, b) in enumerate(segs):
        d = b - a
        f = min(0.015, d / 4)
        parts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS,fps=30[v{i}];"
                     f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d={f:.3f},afade=t=out:st={d - f:.3f}:d={f:.3f}[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    fc = "".join(parts) + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(src), "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", str(out)], check=True)
    return out


def make(src, workdir, ffmpeg, cfg, pick, language, transcribe, probe_duration):
    """Gibt (geschnittene Datei oder None, info) zurück. None = kein Schnitt nötig."""
    dur = probe_duration(src, ffmpeg)
    segs, info = plan(src, ffmpeg, cfg, pick, dur, language, transcribe)
    simple = len(segs) == 1 and not info["cold_open"]
    if simple:
        return None, info
    out = Path(workdir) / "schnitt.mp4"
    render(src, ffmpeg, segs, out)
    return out, info
