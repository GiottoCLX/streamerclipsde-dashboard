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
    for m, meta in shorts.all_metas(cfg, CHANNEL):
        if meta.get("uploaded") or meta.get("skip") or not (ROOT / meta["file"]).exists():
            continue
        queue.append({"title": meta["title"].replace(" #shorts", ""), "streamer": meta.get("streamer", ""),
                      "slot": slot.strftime("%d.%m. %H:%M")})
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

    data = {
        "generated": now.strftime("%d.%m.%Y %H:%M"), "next_post": next_slot(now).strftime("%H:%M"),
        "last_run": last_run, "status_ok": status_ok, "total": total, "views_24h": views_24h,
        "posted": len(rows), "posted_24h": posted_24h, "avg_watched": avg_watched,
        "best": best, "rows": rows, "series": series, "queue": queue, "skipped": skipped, "log": log_lines,
    }
    page = TEMPLATE.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")) \
                   .replace("<!--STRATEGY-->", strat_html)
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


TEMPLATE = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>StreamerclipsDE – Dashboard</title>
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --series-1: #2a78d6; --wash: rgba(42,120,214,0.10);
  --good: #0ca30c; --good-text: #006300; --warn: #fab219; --crit: #d03b3b;
  --accent: #9146FF;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19; --ink: #f0efec; --ink-2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --series-1: #3987e5; --wash: rgba(57,135,229,0.12); --good-text: #0ca30c;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
.wrap { max-width: 1180px; margin: 0 auto; padding: 28px 20px 60px; }
header { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 20px; margin-bottom: 24px; }
header h1 { font-size: 22px; margin: 0; font-weight: 650; }
header h1 span { display: inline-block; width: 10px; height: 10px; border-radius: 3px; background: var(--accent); margin-right: 8px; }
.meta { color: var(--ink-2); font-size: 13px; }
.pill { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px;
  font-size: 13px; border: 1px solid var(--border); background: var(--surface); }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
nav { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 20px; }
nav a { color: var(--ink-2); text-decoration: none; font-size: 13px; padding: 4px 10px; border-radius: 8px; border: 1px solid var(--border); background: var(--surface); }
nav a:hover { color: var(--ink); }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 18px 20px; }
.grid { display: grid; gap: 14px; }
.kpis { grid-template-columns: 1.4fr repeat(4, 1fr); margin-bottom: 14px; }
@media (max-width: 900px) { .kpis { grid-template-columns: 1fr 1fr; } .kpis .hero { grid-column: 1 / -1; } }
.label { color: var(--ink-2); font-size: 13px; }
.value { font-size: 26px; font-weight: 620; margin-top: 2px; }
.hero .value { font-size: 52px; line-height: 1.1; }
.sub { color: var(--muted); font-size: 12.5px; margin-top: 2px; }
h2 { font-size: 16px; margin: 0 0 4px; font-weight: 640; }
section { margin-top: 26px; scroll-margin-top: 16px; }
.two { grid-template-columns: 1fr 1fr; }
@media (max-width: 900px) { .two { grid-template-columns: 1fr; } }
svg text { fill: var(--muted); font-size: 11px; font-variant-numeric: tabular-nums; }
.tip { position: fixed; pointer-events: none; background: var(--surface); color: var(--ink); border: 1px solid var(--border);
  border-radius: 8px; padding: 7px 10px; font-size: 12.5px; box-shadow: 0 4px 16px rgba(0,0,0,.12); display: none; max-width: 320px; z-index: 10; }
.tip b { font-weight: 620; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; color: var(--ink-2); font-weight: 560; padding: 8px 8px; border-bottom: 1px solid var(--axis); white-space: nowrap; cursor: pointer; user-select: none; }
td { padding: 8px 8px; border-bottom: 1px solid var(--grid); vertical-align: top; }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.scroll { overflow-x: auto; }
a { color: var(--series-1); }
.tag { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; font-size: 12px; }
.tag .ic { font-weight: 700; }
.top .ic { color: var(--good-text); } .flop .ic { color: var(--crit); } .test .ic, .mid .ic { color: var(--muted); }
.small { color: var(--muted); font-size: 12px; }
.strategy h1 { font-size: 18px; margin-top: 0; }
.strategy h2 { font-size: 15.5px; margin: 22px 0 8px; padding-top: 14px; border-top: 1px solid var(--grid); }
.strategy table th { cursor: default; }
.strategy code { background: var(--page); padding: 1px 5px; border-radius: 5px; font-size: 12.5px; }
.strategy li { margin: 6px 0; }
.log { font: 12.5px/1.6 ui-monospace, Consolas, monospace; white-space: pre-wrap; color: var(--ink-2); }
.bars { margin-top: 10px; }
.bar-row { display: grid; grid-template-columns: minmax(0, 42%) 1fr; gap: 10px; align-items: center; padding: 5px 0; outline: none; }
.bl { font-size: 12.5px; color: var(--ink-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: right; }
.bt { display: flex; align-items: center; gap: 6px; border-left: 1px solid var(--axis); min-height: 18px; }
.bar { height: 16px; max-width: calc(100% - 48px); background: var(--series-1); border-radius: 0 4px 4px 0; }
.bv { font-size: 12px; color: var(--ink); font-variant-numeric: tabular-nums; }
.bar-row:hover .bar, .bar-row:focus .bar { opacity: .8; }
#t-shorts td:nth-child(2) { min-width: 230px; }
.kpis .card:last-child .value { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
ol.queue { margin: 0; padding-left: 20px; } ol.queue li { margin: 6px 0; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1><span></span>StreamerclipsDE · Dashboard</h1>
    <span class="pill" id="status"></span>
    <span class="meta" id="gen"></span>
  </header>
  <nav>
    <a href="#zahlen">Zahlen</a><a href="#shorts">Alle Shorts</a><a href="#queue">Warteschlange</a>
    <a href="#strategie">Strategie</a><a href="#log">Verlauf</a>
  </nav>

  <div class="grid kpis" id="zahlen">
    <div class="card hero"><div class="label">Aufrufe gesamt</div><div class="value" id="k-total"></div><div class="sub" id="k-total-sub"></div></div>
    <div class="card"><div class="label">Aufrufe letzte 24 h</div><div class="value" id="k-24h"></div></div>
    <div class="card"><div class="label">Shorts gepostet</div><div class="value" id="k-posted"></div><div class="sub" id="k-posted-sub"></div></div>
    <div class="card"><div class="label">Ø angesehen (statt weggewischt)</div><div class="value" id="k-watched"></div><div class="sub">Ziel ≥ 70 %</div></div>
    <div class="card"><div class="label">Bester Short</div><div class="value" style="font-size:17px;line-height:1.3" id="k-best"></div><div class="sub" id="k-best-sub"></div></div>
  </div>

  <div class="grid two">
    <div class="card"><h2>Aufrufe gesamt über Zeit</h2><div class="small">Summe aller Shorts zu jedem Messzeitpunkt</div><div id="c-line"></div></div>
    <div class="card"><h2>Aufrufe pro Short</h2><div class="small">Sortiert nach Aufrufen</div><div id="c-bars"></div></div>
  </div>

  <section id="shorts" class="card">
    <h2>Alle Shorts</h2>
    <div class="small" style="margin-bottom:8px">Spaltenkopf anklicken zum Sortieren. „Angesehen“ = Anteil, der nicht weggewischt hat (YouTube Studio). Ø Sek. = durchschnittliche Wiedergabe pro Aufruf.</div>
    <div class="scroll"><table id="t-shorts"></table></div>
  </section>

  <div class="grid two" style="margin-top:14px" id="queue">
    <div class="card"><h2>Warteschlange</h2><div class="small" style="margin-bottom:8px">Wird alle 2 Stunden gepostet · nächster Post ca. <span id="next"></span></div><ol class="queue" id="q"></ol></div>
    <div class="card"><h2>Aussortiert</h2><div class="small" style="margin-bottom:8px">Fertig geschnitten, aber nicht gepostet</div><ul id="sk" style="margin:0;padding-left:20px"></ul></div>
  </div>

  <section id="strategie" class="card strategy"><!--STRATEGY--></section>

  <section id="log" class="card"><h2>Verlauf der Läufe</h2><div class="small" style="margin-bottom:8px">Neueste zuerst</div><div class="log" id="logbox"></div></section>
</div>
<div class="tip" id="tip"></div>
<script>
const D = /*DATA*/null;
const $ = id => document.getElementById(id);
const fmt = n => n == null ? '–' : n.toLocaleString('de-DE');
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const tip = $('tip');
function showTip(ev, h) { tip.innerHTML = h; tip.style.display = 'block'; moveTip(ev); }
function moveTip(ev) { const x = Math.min(ev.clientX + 14, innerWidth - tip.offsetWidth - 8); tip.style.left = x + 'px'; tip.style.top = (ev.clientY + 14) + 'px'; }
function hideTip() { tip.style.display = 'none'; }

const lr = D.last_run ? D.last_run.match(/\d{4}-(\d\d)-(\d\d) (\d\d:\d\d)/) : null;
$('gen').textContent = 'Stand ' + D.generated + (lr ? ` · letzter Lauf ${lr[2]}.${lr[1]}. ${lr[3]}` : '');
$('status').innerHTML = D.status_ok
  ? '<span class="dot" style="background:var(--good)"></span><b>✓</b> Läuft – postet alle 2 h'
  : '<span class="dot" style="background:var(--crit)"></span><b>!</b> Letzter Lauf ist länger her – PC/App/Chrome prüfen';
$('k-total').textContent = fmt(D.total);
$('k-total-sub').textContent = D.posted ? 'Ø ' + fmt(Math.round(D.total / D.posted)) + ' pro Short' : '';
$('k-24h').textContent = fmt(D.views_24h);
$('k-posted').textContent = fmt(D.posted);
$('k-posted-sub').textContent = D.posted_24h + ' in den letzten 24 h';
$('k-watched').textContent = D.avg_watched == null ? '–' : D.avg_watched.toLocaleString('de-DE') + ' %';
if (D.best) { $('k-best').textContent = D.best.title; $('k-best-sub').textContent = fmt(D.best.views) + ' Aufrufe · ' + D.best.streamer; }
$('next').textContent = D.next_post + ' Uhr';

// ---- line chart: total views over time
(function () {
  const el = $('c-line'), s = D.series;
  if (s.length < 2) { el.innerHTML = '<p class="small">Noch zu wenige Messpunkte – füllt sich mit jedem Lauf.</p>'; return; }
  const W = 540, H = 230, L = 46, R = 14, T = 14, B = 26;
  const ts = s.map(p => new Date(p.t).getTime()), t0 = Math.min(...ts), t1 = Math.max(...ts);
  const vmax = Math.max(...s.map(p => p.views)) || 1;
  const step = Math.pow(10, Math.floor(Math.log10(vmax))) * (vmax / Math.pow(10, Math.floor(Math.log10(vmax))) > 5 ? 2 : 1);
  const ymax = Math.ceil(vmax / step) * step;
  const x = t => L + (t - t0) / ((t1 - t0) || 1) * (W - L - R), y = v => T + (1 - v / ymax) * (H - T - B);
  let g = '';
  for (let v = 0; v <= ymax; v += step) g += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--grid)"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${fmt(v)}</text>`;
  const fmtT = t => { const d = new Date(t); return d.toLocaleDateString('de-DE', {day:'2-digit', month:'2-digit'}) + ' ' + d.toLocaleTimeString('de-DE', {hour:'2-digit', minute:'2-digit'}); };
  g += `<text x="${L}" y="${H - 6}">${fmtT(t0)}</text><text x="${W - R}" y="${H - 6}" text-anchor="end">${fmtT(t1)}</text>`;
  const pts = s.map((p, i) => `${x(ts[i])},${y(p.views)}`).join(' ');
  const area = `${x(ts[0])},${y(0)} ${pts} ${x(ts[ts.length - 1])},${y(0)}`;
  const last = s[s.length - 1];
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Gesamtaufrufe über Zeit, aktuell ${fmt(last.views)}">
    ${g}<line x1="${L}" x2="${W - R}" y1="${y(0)}" y2="${y(0)}" stroke="var(--axis)"/>
    <polygon points="${area}" fill="var(--wash)"/>
    <polyline points="${pts}" fill="none" stroke="var(--series-1)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    <line id="xh" y1="${T}" y2="${H - B}" stroke="var(--axis)" visibility="hidden"/>
    <circle id="xd" r="4.5" fill="var(--series-1)" stroke="var(--surface)" stroke-width="2" visibility="hidden"/>
    <circle cx="${x(ts[ts.length - 1])}" cy="${y(last.views)}" r="4.5" fill="var(--series-1)" stroke="var(--surface)" stroke-width="2"/>
    <rect id="hit" x="${L}" y="${T}" width="${W - L - R}" height="${H - T - B}" fill="transparent"/></svg>`;
  const svg = el.querySelector('svg'), hit = svg.querySelector('#hit'), xh = svg.querySelector('#xh'), xd = svg.querySelector('#xd');
  hit.addEventListener('mousemove', ev => {
    const r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) / r.width * W;
    let i = 0, best = Infinity; ts.forEach((t, k) => { const d = Math.abs(x(t) - px); if (d < best) { best = d; i = k; } });
    xh.setAttribute('x1', x(ts[i])); xh.setAttribute('x2', x(ts[i])); xh.setAttribute('visibility', 'visible');
    xd.setAttribute('cx', x(ts[i])); xd.setAttribute('cy', y(s[i].views)); xd.setAttribute('visibility', 'visible');
    showTip(ev, `<b>${fmt(s[i].views)}</b> Aufrufe<br><span class="small">${fmtT(ts[i])}</span>`);
  });
  hit.addEventListener('mouseleave', () => { xh.setAttribute('visibility', 'hidden'); xd.setAttribute('visibility', 'hidden'); hideTip(); });
})();

// ---- horizontal bars: views per short (HTML, damit Beschriftung auf dem Handy lesbar bleibt)
(function () {
  const el = $('c-bars'), rows = [...D.rows].sort((a, b) => b.views - a.views);
  if (!rows.length) { el.innerHTML = '<p class="small">Noch keine Daten.</p>'; return; }
  const vmax = Math.max(...rows.map(r => r.views)) || 1;
  el.innerHTML = '<div class="bars" role="list" aria-label="Aufrufe pro Short">' + rows.map((r, i) =>
    `<div class="bar-row" role="listitem" tabindex="0" data-i="${i}">
       <div class="bl">${esc(r.title)}</div>
       <div class="bt"><div class="bar" style="width:${r.views ? Math.max(r.views / vmax * 100, 1) : 0}%"></div><span class="bv">${fmt(r.views)}</span></div>
     </div>`).join('') + '</div>';
  el.querySelectorAll('.bar-row').forEach(n => {
    const r = rows[+n.dataset.i];
    const h = `<b>${esc(r.title)}</b><br>${fmt(r.views)} Aufrufe · ${r.angesehen == null ? '–' : r.angesehen + ' %'} angesehen<br><span class="small">${esc(r.streamer)} · ${r.verdict}</span>`;
    n.addEventListener('mousemove', ev => showTip(ev, h)); n.addEventListener('mouseleave', hideTip);
  });
})();

// ---- table
const cols = [
  ['uploaded_at', 'Gepostet', r => r.uploaded_at ? new Date(r.uploaded_at).toLocaleString('de-DE', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'}) : '–'],
  ['title', 'Short', r => `<a href="https://youtube.com/shorts/${r.id}" target="_blank" rel="noopener">${esc(r.title)}</a>${r.experiment ? `<div class="small">Experiment: ${esc(r.experiment)}</div>` : ''}`],
  ['streamer', 'Streamer', r => esc(r.streamer)],
  ['verdict', 'Bewertung', r => `<span class="tag ${r.cls}"><span class="ic">${{top:'▲', flop:'▼', test:'…', mid:'–'}[r.cls]}</span>${r.verdict}</span>`],
  ['views', 'Aufrufe', r => fmt(r.views), 1], ['vph', 'pro Std', r => fmt(r.vph), 1],
  ['angesehen', 'Angesehen', r => r.angesehen == null ? '–' : r.angesehen.toLocaleString('de-DE') + ' %', 1],
  ['avd', 'Ø Sek.', r => r.avd == null ? '–' : r.avd.toLocaleString('de-DE'), 1],
  ['dur', 'Länge', r => r.dur == null ? '–' : Math.round(r.dur) + ' s', 1],
  ['like_rate', 'Likes', r => `${fmt(r.likes)} <span class="small">(${r.like_rate.toLocaleString('de-DE')} %)</span>`, 1],
  ['design', 'Design', r => esc(r.design)],
];
let sortKey = 'uploaded_at', sortDir = -1;
function renderTable() {
  const rows = [...D.rows].sort((a, b) => { const x = a[sortKey] ?? -1, y = b[sortKey] ?? -1; return (x > y ? 1 : x < y ? -1 : 0) * sortDir; });
  $('t-shorts').innerHTML = '<thead><tr>' + cols.map(c => `<th class="${c[3] ? 'n' : ''}" data-k="${c[0]}">${c[1]}${sortKey === c[0] ? (sortDir > 0 ? ' ↑' : ' ↓') : ''}</th>`).join('') + '</tr></thead><tbody>' +
    rows.map(r => '<tr>' + cols.map(c => `<td class="${c[3] ? 'n' : ''}">${c[2](r)}</td>`).join('') + '</tr>').join('') + '</tbody>';
  $('t-shorts').querySelectorAll('th').forEach(th => th.onclick = () => { const k = th.dataset.k; sortDir = sortKey === k ? -sortDir : -1; sortKey = k; renderTable(); });
}
renderTable();

$('q').innerHTML = D.queue.length ? D.queue.map(q => `<li><b>${esc(q.slot)}</b> – ${esc(q.title)}</li>`).join('') : '<li class="small">Leer – der nächste Lauf sucht neue Clips.</li>';
$('sk').innerHTML = D.skipped.length ? D.skipped.map(s => `<li>${esc(s.title)} <span class="small">– ${esc(s.reason)}</span></li>`).join('') : '<li class="small">Nichts aussortiert.</li>';
$('logbox').textContent = D.log.length ? D.log.join('\n') : 'Noch keine Läufe.';
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
    if "--push" in sys.argv:
        push()
