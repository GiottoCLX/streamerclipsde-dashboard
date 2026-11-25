"""Baut das Dashboard docs/index.html aus stats, Studio-Werten, Warteschlange, Log und STRATEGIE.md.

    python dashboard.py          -> nur bauen
    python dashboard.py --push   -> bauen, committen und zu GitHub pushen (GitHub Pages)
"""
import datetime as dt
import html
import json
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import shorts  # noqa: E402

CHANNEL = "kanal1"
POST_EVERY_H = 2


def load_json(p, default):
    return json.loads(p.read_text("utf-8-sig")) if p.exists() else default


def verdict(e):
    perf = e.get("perf") or {}
    ang = perf.get("angesehen")
    views, age = e.get("views", 0), e.get("age_h", 0)
    if views >= 100 and (ang is None or ang >= 55):
        return "top", "Gewinner"
    if ang is not None and views >= 3 and ang < 45:
        return "flop", "Flop"
    if age >= 24 and views < 10:
        return "flop", "Im Test durchgefallen"
    if age < 24 and views < 50:
        return "test", "Test läuft"
    return "mid", "Mittel"


def total_series(hist):
    """Gesamtaufrufe zu jedem Messzeitpunkt (letzter bekannter Stand je Short)."""
    points = sorted({s["t"] for e in hist.values() for s in e.get("snapshots", [])})
    out = []
    for t in points:
        tot = 0
        for e in hist.values():
            known = [s["views"] for s in e.get("snapshots", []) if s["t"] <= t]
            tot += known[-1] if known else 0
        out.append({"t": t, "views": tot})
    return out


def next_slot(now):
    h = (now.hour // POST_EVERY_H + 1) * POST_EVERY_H
    base = now.replace(minute=0, second=0, microsecond=0)
    return base + dt.timedelta(hours=h - now.hour)


def build():
    cfg = shorts.load_config()
    now = dt.datetime.now()
    hist = load_json(ROOT / "stats" / f"{CHANNEL}.json", {})
    rows = []
    for vid, e in hist.items():
        cls, label = verdict(e)
        perf = e.get("perf") or {}
        rows.append({
            "id": vid, "title": e["title"].replace(" #shorts", ""), "streamer": e.get("streamer") or "",
            "uploaded_at": e.get("uploaded_at") or "", "dur": e.get("dur"), "views": e.get("views", 0),
            "vph": e.get("views_per_h", 0), "like_rate": e.get("like_rate", 0), "likes": e.get("likes", 0),
            "angesehen": perf.get("angesehen"), "weggewischt": perf.get("weggewischt"), "avd": perf.get("avd"),
            "design": e.get("design", ""), "experiment": e.get("experiment") or "", "cls": cls, "verdict": label,
            "headline": e.get("headline") or "", "clip_title": e.get("clip_title") or "",
        })
    rows.sort(key=lambda r: r["uploaded_at"], reverse=True)

    series = total_series(hist)
    total = series[-1]["views"] if series else 0
    day_ago = (now - dt.timedelta(hours=24)).isoformat(timespec="minutes")
    base = [p for p in series if p["t"] <= day_ago]
    views_24h = total - (base[-1]["views"] if base else 0)
    watched = [r["angesehen"] for r in rows if r["angesehen"] is not None and r["views"] >= 20]
    avg_watched = round(sum(watched) / len(watched), 1) if watched else None
    best = max(rows, key=lambda r: r["views"]) if rows else None
    posted_24h = sum(1 for r in rows if r["uploaded_at"] >= day_ago)

    queue = []
    slot = next_slot(now)
    picks = shorts._headlines()
    for m, meta in shorts.all_metas(cfg, CHANNEL):
        if meta.get("uploaded") or meta.get("skip") or not (ROOT / meta["file"]).exists():
            continue
        pk = picks.get(str(meta.get("source", {}).get("id", "")), {})
        queue.append({"title": meta["title"].replace(" #shorts", ""), "streamer": meta.get("streamer", ""),
                      "slot": slot.strftime("%d.%m. %H:%M"), "note": pk.get("note"), "warum": pk.get("warum", "")})
        slot += dt.timedelta(hours=POST_EVERY_H)
    skipped = [{"title": meta["title"].replace(" #shorts", ""), "reason": meta["skip"]}
               for m, meta in shorts.all_metas(cfg, CHANNEL) if meta.get("skip") and not meta.get("uploaded")]

    log_lines = []
    lp = ROOT / "logs" / "posting.log"
    if lp.exists():
        log_lines = [l for l in lp.read_text("utf-8-sig").splitlines() if l.strip()][-20:][::-1]
    last_run = log_lines[0].split(" | ")[0] if log_lines else None
    status_ok = True
    if last_run:
        try:
            status_ok = (now - dt.datetime.strptime(last_run, "%Y-%m-%d %H:%M")) < dt.timedelta(hours=POST_EVERY_H * 2 + 1)
        except ValueError:
            pass

    strat_md = (ROOT / "STRATEGIE.md").read_text("utf-8-sig") if (ROOT / "STRATEGIE.md").exists() else ""
    strat_html = markdown.markdown(strat_md, extensions=["tables"])
    rules_md = (ROOT / "REGELN.md").read_text("utf-8-sig") if (ROOT / "REGELN.md").exists() else ""
    rules_html = markdown.markdown(rules_md, extensions=["tables"])
    import live as live_mod
    rules_ver = live_mod.rules_version()
    try:
        switches = live_mod.parse_rules()
    except Exception:
        switches = None

    data = {
        "repo": REPO, "rules_ver": rules_ver, "switches": switches,
        "live": load_json(ROOT / "docs" / "live.json", None),
        "generated": now.strftime("%d.%m.%Y %H:%M"), "next_post": next_slot(now).strftime("%H:%M"),
        "last_run": last_run, "status_ok": status_ok, "total": total, "views_24h": views_24h,
        "posted": len(rows), "posted_24h": posted_24h, "avg_watched": avg_watched,
        "best": best, "rows": rows, "series": series, "queue": queue, "skipped": skipped, "log": log_lines,
    }
    page = TEMPLATE_FILE.read_text("utf-8").replace("/*DATA*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")) \
                   .replace("<!--STRATEGY-->", strat_html).replace("<!--RULES-->", rules_html)
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, "utf-8")
    (ROOT / "docs" / ".nojekyll").write_text("", "utf-8")
    print(f"Dashboard gebaut -> {out.relative_to(ROOT)}  ({len(rows)} Shorts, {total} Aufrufe)")


def push():
    def git(*a, check=True):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=check)
    git("add", "-A")
    if not git("status", "--porcelain").stdout.strip():
        print("Nichts Neues zu pushen.")
        return
    stamp = dt.datetime.now().strftime("%d.%m.%Y %H:%M")
    git("commit", "-m", f"Dashboard-Update {stamp}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    git("pull", "--rebase", "--autostash", "-q", check=False)  # Regel-Änderungen von GitHub übernehmen
    r = git("push", "-q", check=False)
    print("gepusht" if r.returncode == 0 else f"Push fehlgeschlagen: {r.stderr.strip()[:300]}")
    ensure_pages()


REPO = "GiottoCLX/streamerclipsde-dashboard"


def ensure_pages():
    """Schaltet GitHub Pages (main /docs) ein, falls noch nicht aktiv."""
    gh = lambda *a, **kw: subprocess.run(["gh", "api", *a], capture_output=True, text=True, encoding="utf-8", **kw)
    if gh(f"repos/{REPO}/pages").returncode == 0:
        print(f"Dashboard: https://{REPO.split('/')[0].lower()}.github.io/{REPO.split('/')[1]}/")
        return
    r = gh("-X", "POST", f"repos/{REPO}/pages", "--input", "-",
           input=json.dumps({"build_type": "legacy", "source": {"branch": "main", "path": "/docs"}}))
    print("GitHub Pages eingeschaltet." if r.returncode == 0
          else f"GitHub Pages konnte (noch) nicht eingeschaltet werden: {(r.stderr or r.stdout).strip()[:200]}")


TEMPLATE_FILE = ROOT / "dashboard_template.html"


if __name__ == "__main__":
    build()
    if "--push" in sys.argv:
        push()
