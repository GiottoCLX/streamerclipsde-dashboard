# Technik-Anleitung für die Läufe (StreamerclipsDE)

**Was** wann passiert, steht in `REGELN.md` – die hat immer Vorrang. Hier steht nur, **wie** die einzelnen Schritte technisch gehen.
Ordner: `C:\Users\diene\Desktop\Shorts Automatik` · Python: `.\.venv\Scripts\python.exe` (unten kurz `py`).

**Zwei Kanäle:** Jeder Lauf gehört zu genau einem Kanal. Überall `--channel <kanal>` mitgeben (`live.py`, `browser-queue`, `scout`, `stats`, `status`).

| | kanal1 | kanal4 |
|---|---|---|
| Name | StreamerclipsDE (deutsch) | Stream Clips Daily (englisch) |
| Studio | `https://studio.youtube.com/channel/UC5wsIwWO9EMifAyY9oLyRrQ/videos/short` | `https://studio.youtube.com/channel/UCItdS5ca1wZv4FBEM_6IarQ/videos/short` |
| Prüfen, dass Studio zeigt | StreamerclipsDE | Stream Clips Daily |
| Log-Zeile beginnt nach der Zeit mit | – | `[Stream Clips Daily]` |
| Sprache Pick (headline/title/warum) | Deutsch (warum: Deutsch) | headline/title **Englisch**, warum Deutsch |

Englische Clips haben oft schon **eingebrannte Untertitel** im Bild (z. B. Kai Cenat, Jynxzi) → im Pick `"subtitles": false` setzen, sonst doppelt. Kein N-Wort und keine Beleidigungen im Clip (Untertitel würden es groß zeigen).

**Live-Meldungen:** Vor jedem Schritt `py live.py step "<was jetzt passiert>"` – kurz und auf Deutsch, so dass der Nutzer versteht, was gerade läuft (z. B. „Lade Short hoch: Monte – Gerechte Strafe“). Probleme mit `py live.py warn "<Problem>"`.

## Schritt 1 – Start
`py live.py start "Lauf HH:MM"` (holt die neueste REGELN.md von GitHub). Dann `REGELN.md` und `STRATEGIE.md` lesen.

## Schritt 2 – Prüfen
`py live.py check` → JSON mit `may_post`, `reason` und allen Schaltern (`posts_per_run`, `stock`, `clip_len`, `expire_h`, `streamers`, `missing_streamers`).
- `missing_streamers` nicht leer → je Streamer einen `[[streamer]]`-Block (name, twitch, channel = "kanal1", zoom = 1.3) in `config.toml` ergänzen.
- `pause: true` → nur Schritt 4 (nur `stats`) und Schritt 7.

## Schritt 3 – Posten (nur wenn `may_post`)
1. `py shorts.py browser-queue --channel kanal1 --limit 3` → `queue\kanal1.json` (ältester zuerst, `file` = <10-MB-Version).
2. Claude in Chrome: Werkzeuge in EINEM ToolSearch laden (tabs_context_mcp, tabs_create_mcp, navigate, computer, find, javascript_tool, file_upload, get_page_text, browser_batch, tabs_close_mcp), eigenen Tab öffnen:
   `https://studio.youtube.com/channel/UC5wsIwWO9EMifAyY9oLyRrQ/videos/short`
   - Steht dort **StreamerclipsDE**? Sonst nicht posten (`live.py warn`).
   - Titel schon in der Liste? → nicht hochladen, ID aus der Liste holen, nur `mark-uploaded`.
3. Inhalt von `studio_upload.js` per javascript_tool ausführen, dann je ein Aufruf:
   `await __openUpload()` → `find` „hidden file input“ → `file_upload` (Pfad aus `file`) → ~8 s warten → `__setStudio(title, description)` (muss `{title, descLen}` liefern) → `await __toPublic()` (`kids:true, public:true`) → `await __publish()`.
4. Video-ID aus der Shorts-Liste (`a[href*="/video/"]`) → `py shorts.py mark-uploaded "<meta>" <ID>` → `py shorts.py status <ID>` muss `public` zeigen. Tab schließen.

## Schritt 4 – Zahlen auswerten
1. `py shorts.py stats`
2. Studio-Werte für Shorts, die 2–72 h alt sind und deren `perf.checked_at` älter als 6 h ist (max. 4, älteste zuerst): navigate zu `https://studio.youtube.com/video/<ID>/analytics/tab-overview/period-default`, `__perf` aus `studio_upload.js` definieren, `await __perf()` (pro Video ein eigener Aufruf) → `py shorts.py perf <ID> aufrufe=… angesehen=… weggewischt=… avd=… likes=…`
3. Gewinner (viele Aufrufe/Std UND angesehen ≥ 55 %) mit Verlierern (< 10 Aufrufe nach 24 h oder angesehen < 45 %) vergleichen: Einstieg (erste 2 s), Länge, Streamer, Talk/Gameplay, Headline, Layout, Uhrzeit, `experiment`.
4. `STRATEGIE.md` pflegen (Regeln nur mit Zahlen-Beleg, Rest als Experiment, Zeile ins Log). Ideen, die eine Änderung an `REGELN.md` bräuchten → unter „Vorschläge für REGELN.md“ in `STRATEGIE.md` eintragen, nicht selbst ändern.

## Schritt 5 – Vorrat prüfen
Fertige, ungepostete Shorts (`.json` ohne `uploaded`/`skip`) gegen REGELN.md prüfen. Älter als `expire_h` oder unpassend → `"skip": "<Grund>"` in die .json.

## Schritt 6 – Nächsten Clip vorbereiten
1. `py shorts.py scout --channel kanal1 --range 24hr --limit 8` (zu wenig → `--range 7d --limit 5`).
2. `scout\<datum>.txt` lesen (Abschnitt StreamerclipsDE) und nach REGELN.md Abschnitt 3 auswählen (Qualitäts-Check, Note ≥ 8). Nur Streamer aus dem Schalter. Bei Kandidaten, die vom Text her gut wirken, vor dem Pick auch das Bild ansehen: rendern + `sheet` – erst dann die endgültige Note.
3. `picks\<datum>_<HHMM>.json`: `[{"id": "...", "headline": "...", "title": "...", "start": s, "end": s, "note": 8, "warum": "1 Satz: was passiert und warum es lustig/krass/cool ist", "experiment": "..."}]` – Länge laut Schalter `clip_len`.
4. `py shorts.py render picks\<datei>.json`
5. `py shorts.py sheet "<mp4>"` → PNG mit Read ansehen und nach REGELN.md Abschnitt 4 prüfen. Nicht gut → start/end ändern und neu rendern (vorher die Datei in `klein\` löschen) oder `skip`.

## Schritt 7 – Abschluss
1. Log-Zeile an `logs\posting.log`: `<YYYY-MM-DD HH:MM> | gepostet: <Titel> <ID oder -> | bereit: <Anzahl> | Notiz`
2. `py dashboard.py --push`
3. `py live.py done "<1 Satz: was gepostet, was bereitliegt, Probleme>"`
4. Kurzer Bericht auf Deutsch.

Bei Abbruch: `py live.py fail "<Grund>"` (und trotzdem Log-Zeile + Dashboard, wenn möglich).
