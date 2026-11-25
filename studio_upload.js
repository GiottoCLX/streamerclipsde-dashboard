// Hilfsfunktionen für Uploads in YouTube Studio (deutsche Oberfläche), per Claude in Chrome ausführen.
// Ablauf pro Video:
//   1. await __openUpload()                       -> öffnet "Videos hochladen" (schließt vorher Erfolgs-Dialoge)
//   2. find "hidden file input" + file_upload       -> Datei aus queue/<kanal>.json ("file", < 10 MB)
//   3. ~8 s warten, dann __setStudio(titel, beschreibung)  -> muss {title, descLen} zurückgeben
//   4. await __toPublic()                          -> "nicht für Kinder", 3x Weiter, "Öffentlich"
//   5. await __publish()                           -> klickt Veröffentlichen, gibt {state, link} zurück
//   6. Video-ID ermitteln (link oder Inhalte-Liste) und shorts.py mark-uploaded <meta> <id>

window.__isDoneDlg = d => d.offsetParent && (d.innerText.includes('Video ist veröffentlicht') || d.innerText.includes('Video wird verarbeitet'));

window.__dlg = () => [...document.querySelectorAll('ytcp-uploads-dialog')].reverse()
  .find(d => [...d.querySelectorAll('[aria-label^="Gib einen Titel"]')].some(e => e.offsetParent));

window.__openUpload = async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const d = [...document.querySelectorAll('ytcp-dialog, tp-yt-paper-dialog')].find(__isDoneDlg);
  if (d) { [...d.querySelectorAll('button, ytcp-button')].find(x => x.innerText.trim() === 'Schließen')?.click(); await sleep(1000); }
  const create = document.querySelector('#create-icon') || [...document.querySelectorAll('button')].find(b => b.getAttribute('aria-label') === 'Erstellen');
  if (!create) return 'create button not found';
  create.click(); await sleep(800);
  const item = [...document.querySelectorAll('tp-yt-paper-item, [role="menuitem"]')].find(x => x.innerText.trim() === 'Videos hochladen' && x.offsetParent);
  if (!item) return 'menu item not found';
  item.click(); await sleep(1500);
  return true;
};

window.__setStudio = (title, desc) => {
  const dlg = __dlg(); if (!dlg) return 'no dialog (Upload noch nicht bereit? kurz warten und erneut)';
  const vis = sel => [...dlg.querySelectorAll(sel)].find(e => e.offsetParent);
  const set = (el, text) => { el.focus(); document.execCommand('selectAll', false, null); document.execCommand('insertText', false, text); el.dispatchEvent(new Event('input', {bubbles: true})); el.blur(); };
  const t = vis('[aria-label^="Gib einen Titel"]'), d = vis('[aria-label^="Erzähle Nutzern"]');
  if (!t || !d) return 'not found: ' + !!t + ' ' + !!d;
  set(t, title); set(d, desc);
  return {title: t.innerText, descLen: d.innerText.length};
};

window.__toPublic = async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const dlg = __dlg(); if (!dlg) return 'no dialog';
  const kids = dlg.querySelector('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]');
  if (!kids) return 'kids radio not found';
  kids.click(); await sleep(500);
  for (let i = 0; i < 3; i++) { dlg.querySelector('#next-button').click(); await sleep(1200); }
  const pub = dlg.querySelector('tp-yt-paper-radio-button[name="PUBLIC"]');
  if (!pub) return 'public radio not found';
  pub.click(); await sleep(500);
  return {kids: kids.hasAttribute('checked'), public: pub.hasAttribute('checked'), done: dlg.querySelector('#done-button')?.innerText.trim()};
};

window.__publish = async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const dlg = __dlg();
  const link = dlg ? [...dlg.querySelectorAll('a')].map(a => a.href.split('?')[0]).find(h => h.includes('/shorts/') || h.includes('youtu.be/')) : null;
  const btn = [...document.querySelectorAll('ytcp-uploads-dialog #done-button')].find(b => b.offsetParent);
  if (!btn) return 'no done button';
  btn.click();
  for (let i = 0; i < 25; i++) {
    await sleep(1000);
    const d = [...document.querySelectorAll('ytcp-dialog, tp-yt-paper-dialog')].find(__isDoneDlg);
    if (d) return {state: d.innerText.includes('veröffentlicht') ? 'veröffentlicht' : 'wird verarbeitet, danach öffentlich', link};
  }
  return {state: 'timeout', link};
};

// Performance eines Shorts aus der Studio-Analyse lesen (vorher zu
// https://studio.youtube.com/video/<ID>/analytics/tab-overview/period-default navigieren).
// Liefert {aufrufe, stunden, angesehen, weggewischt, likes, avd} – avd = Ø Sekunden pro Aufruf.
window.__perf = async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  await sleep(4000);
  [...document.querySelectorAll('tp-yt-paper-tab, [role="tab"]')].find(x => x.innerText.trim() === 'Engagement')?.click();
  await sleep(4000);
  const t = document.body.innerText.replace(/\n+/g, ' | ');
  const num = s => s == null ? null : parseFloat(s.replace(/\./g, '').replace(',', '.'));
  const m = re => { const x = t.match(re); return x ? num(x[1]) : null; };
  const r = {
    aufrufe: m(/Aufrufe \| ([\d.]+) \|/),
    stunden: m(/Wiedergabezeit \(Stunden\) \| ([\d.,]+)/),
    angesehen: m(/([\d,]+)\s*%\s*\|\s*(?:Bis zum Ende angesehen|Angesehen)/),
    weggewischt: m(/([\d,]+)\s*%\s*\|\s*Weggewischt/),
    likes: m(/Likes \| Seit Veröffentlichung \| ([\d.]+)/),
  };
  if (r.aufrufe && r.stunden != null) r.avd = Math.round(r.stunden * 3600 / r.aufrufe * 10) / 10;
  return r;
};

'studio helpers loaded';
