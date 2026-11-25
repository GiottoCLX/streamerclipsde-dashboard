"""Live-Status fürs Dashboard + Regel-Prüfung.

    python live.py start "Lauf 22:00"        -> neue Runde, neueste REGELN.md von GitHub holen
    python live.py step  "Upload läuft"      -> Schritt melden
    python live.py warn  "Chrome nicht da"   -> Warnung melden (Lauf geht weiter)
    python live.py done  "1 Short gepostet"  -> Lauf fertig
    python live.py fail  "Grund"             -> Lauf abgebrochen
    python live.py check                     -> Schalter aus REGELN.md lesen: darf jetzt gepostet werden?

Schreibt docs/live.json und pusht nur diese Datei (das Dashboard fragt sie alle 30 s ab).
--no-push: nur lokal schreiben (zum Testen).
"""
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = ROOT / "docs" / "live.json"
RULES = ROOT / "REGELN.md"
KEEP_RUNS = 15


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")


def now():
    return dt.datetime.now().replace(microsecond=0)


def pull():
    r = git("pull", "--rebase", "--autostash", "-q")
    return r.returncode == 0, (r.stderr or r.stdout).strip()[:200]


def rules_version():
    r = git("log", "-1", "--format=%h|%cI|%cn", "--", "REGELN.md")
    if r.returncode or not r.stdout.strip():
        return None
    h, date, committer = r.stdout.strip().split("|", 2)
    return {"commit": h, "date": date[:16].replace("T", " "), "web": committer == "GitHub"}


def parse_rules():
    """Liest die Schalter (Abschnitt 1) aus REGELN.md."""
    text = RULES.read_text("utf-8-sig")
    sec = text.split("## 1.", 1)[-1].split("\n## ", 1)[0]
    raw = {k.strip().lower(): v.strip() for k, v in re.findall(r"^- \*\*(.+?):\*\*\s*(.+)$", sec, re.M)}

    def get(prefix, default=""):
        return next((v for k, v in raw.items() if k.startswith(prefix)), default)

    def num_range(s, a, b):
        m = re.findall(r"\d+(?::\d+)?", s)
        return (m[0], m[1]) if len(m) >= 2 else (a, b)

    def to_int(s, d):
        m = re.search(r"\d+", s)
        return int(m.group()) if m else d

    t0, t1 = num_range(get("posting-zeiten", "08:00-24:00"), "08:00", "24:00")
    l0, l1 = num_range(get("cliplänge", "15-40"), "15", "40")
    return {
        "pause": get("pause", "nein").lower().startswith(("ja", "an", "true", "1")),
        "posts_per_run": to_int(get("posts pro lauf"), 1),
        "hours": [t0 if ":" in t0 else t0 + ":00", t1 if ":" in t1 else t1 + ":00"],
        "min_gap_min": to_int(get("mindestabstand"), 100),
        "stock": to_int(get("fertige shorts auf vorrat"), 2),
        "clip_len": [int(l0), int(l1)],
        "expire_h": to_int(get("fertige shorts verfallen"), 36),
        "streamers": [s.strip().lower() for s in re.split(r"[,\s]+", get("streamer")) if s.strip()],
    }


def last_post_time():
    sys.path.insert(0, str(ROOT))
    import shorts
    cfg = shorts.load_config()
    times = [dt.datetime.fromisoformat(m["uploaded_at"]) for _, m in shorts.all_metas(cfg, "kanal1")
             if m.get("uploaded") and m.get("uploaded_at")]
    known = {s["twitch"].lower() for s in cfg["streamer"] if s.get("channel", "kanal1") == "kanal1"}
    return (max(times) if times else None), known


def in_hours(t, hours):
    def mins(s):
        h, m = s.split(":")
        return int(h) * 60 + int(m)
    a, b = mins(hours[0]), mins(hours[1])
    x = t.hour * 60 + t.minute
    return a <= x < b if a <= b else (x >= a or x < b)


def cmd_check():
    ok, msg = pull()
    r = parse_rules()
    t = now()
    last, known = last_post_time()
    gap = round((t - last).total_seconds() / 60) if last else None
    reasons = []
    if r["pause"]:
        reasons.append("Pause ist eingeschaltet")
    if not in_hours(t, r["hours"]):
        reasons.append(f"außerhalb der Posting-Zeiten {r['hours'][0]}-{r['hours'][1]}")
    if gap is not None and gap < r["min_gap_min"]:
        reasons.append(f"letzter Post erst vor {gap} Min. (Mindestabstand {r['min_gap_min']})")
    out = {**r, "may_post": not reasons, "reason": "; ".join(reasons) or "Posten erlaubt",
           "minutes_since_last_post": gap, "rules_pulled": ok,
           "missing_streamers": [s for s in r["streamers"] if s not in known],
           "rules_version": rules_version()}
    if not ok:
        out["pull_error"] = msg
    print(json.dumps(out, ensure_ascii=False, indent=1))
    live = load()
    live["check"] = {"t": t.isoformat(), "may_post": out["may_post"], "reason": out["reason"]}
    live["rules"] = out["rules_version"]
    save(live, push="--no-push" not in sys.argv, msg="Live: Regel-Check")


def load():
    if LIVE.exists():
        return json.loads(LIVE.read_text("utf-8-sig"))
    return {"state": "idle", "current": None, "runs": []}


def save(live, push=True, msg="Live-Update"):
    live["updated"] = now().isoformat()
    LIVE.parent.mkdir(exist_ok=True)
    LIVE.write_text(json.dumps(live, ensure_ascii=False, indent=1), "utf-8")
    if not push:
        return
    git("add", "docs/live.json")
    git("commit", "-q", "-m", msg[:72], "-m", "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
        "--", "docs/live.json")
    pull()
    r = git("push", "-q")
    if r.returncode:
        print(f"(Live-Push fehlgeschlagen: {r.stderr.strip()[:200]})")


def add_step(live, text, kind="step"):
    cur = live.get("current")
    if not cur:
        cur = live["current"] = {"title": "Manuell", "started": now().isoformat(), "steps": []}
        live["state"] = "running"
    cur["steps"].append({"t": now().isoformat(), "text": text, "kind": kind})


def finish(live, state, summary):
    cur = live.get("current")
    if cur:
        cur.update(finished=now().isoformat(), state=state, summary=summary)
        live["runs"] = ([cur] + live.get("runs", []))[:KEEP_RUNS]
    live["current"] = None
    live["state"] = "idle" if state == "ok" else "error"
    live["last_summary"] = summary


def main():
    args = [a for a in sys.argv[1:] if a != "--no-push"]
    if not args:
        sys.exit(__doc__)
    cmd, text = args[0], " ".join(args[1:]).strip()
    push = "--no-push" not in sys.argv
    if cmd == "check":
        return cmd_check()
    live = load()
    if cmd == "start":
        if live.get("current"):
            finish(live, "error", "nicht sauber beendet (neuer Lauf gestartet)")
        ok, msg = pull()
        live["current"] = {"title": text or f"Lauf {now():%H:%M}", "started": now().isoformat(), "steps": []}
        live["state"] = "running"
        add_step(live, "Lauf gestartet, neueste Regeln geladen" if ok else f"Regeln konnten nicht von GitHub geladen werden: {msg}",
                 "step" if ok else "warn")
        live["rules"] = rules_version()
    elif cmd in ("step", "warn"):
        add_step(live, text, cmd)
    elif cmd == "done":
        add_step(live, "Fertig", "step")
        finish(live, "ok", text)
    elif cmd == "fail":
        add_step(live, text, "fail")
        finish(live, "fail", text)
    else:
        sys.exit(__doc__)
    save(live, push, f"Live: {cmd} {text}")
    print(f"live: {cmd} {text}")


if __name__ == "__main__":
    main()
