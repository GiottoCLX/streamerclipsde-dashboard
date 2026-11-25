# Posting-Routine StreamerclipsDE – alle 2 Stunden ein Short (über den Browser)

Wunsch des Nutzers: **Posten → sobald online sofort den nächsten Clip suchen → fertig machen → bis zum nächsten Termin warten → posten → …**
Immer über **YouTube Studio im Browser** (Claude in Chrome), nie über die API. Kritisch sein: Wenn ein Clip nicht gut ist, weitersuchen, neu schneiden.

Ordner: `C:\Users\diene\Desktop\Shorts Automatik` · Python: `.\.venv\Scripts\python.exe shorts.py …`
Kanal: **StreamerclipsDE** (Handle @clx_visuals), Kanal-ID `UC5wsIwWO9EMifAyY9oLyRrQ`, config-Schlüssel `kanal1`.
Streamer (Eligella-Bubble): eliasn97, sidneyeweka, niklaswilson, trymacs, montanablack88.

## Teil A – Posten (1 Short pro Lauf)

1. `shorts.py browser-queue --channel kanal1 --limit 3` → `queue\kanal1.json` (ältester fertiger Short zuerst, `file` ist die <10-MB-Version).
   - Leer? → direkt zu Teil B, danach den frisch fertigen Short sofort posten.
2. Chrome: Tab mit `https://studio.youtube.com/channel/UC5wsIwWO9EMifAyY9oLyRrQ/videos/short` öffnen.
   - Prüfen, dass oben/links **StreamerclipsDE** steht. Anderer Kanal oder Login-Seite → NICHT posten, im Bericht melden.
   - **Doppel-Check:** Steht der Titel des Shorts schon in der Shorts-Liste? → nicht nochmal hochladen; ID aus der Liste holen und nur `mark-uploaded` ausführen.
3. Inhalt von `studio_upload.js` per javascript_tool ausführen (lädt die Helfer), dann:
   1. `await __openUpload()`
   2. `find` "hidden file input" → `file_upload` mit dem Pfad aus `file`
   3. ~8 s warten, `__setStudio(title, description)` (Titel/Beschreibung aus queue) → muss `{title, descLen}` liefern, sonst kurz warten und erneut
   4. `await __toPublic()` → `kids:true, public:true`
   5. `await __publish()` → `{state, link}`
4. Video-ID aus `link` (oder aus der Shorts-Liste) holen → `shorts.py mark-uploaded "<meta>" <ID>`
5. `shorts.py status <ID>` → muss `public` sein (bei `uploaded` = wird noch verarbeitet, ok). `rejected`/`failed` → im Bericht melden.

## Teil C – Performance prüfen & lernen (nach dem Posten, vor Teil B)

1. `shorts.py stats` → Aufrufe, Aufrufe/Std, Like-Rate aller öffentlichen Shorts (Verlauf in `stats\kanal1.json`).
2. Studio-Werte holen für Shorts, die **2–72 h alt** sind und deren `perf.checked_at` älter als 6 h ist (max. 4 pro Lauf, die ältesten zuerst):
   - navigate zu `https://studio.youtube.com/video/<ID>/analytics/tab-overview/period-default`
   - die Funktion `__perf` aus `studio_upload.js` definieren und `await __perf()` ausführen (pro Video ein eigener javascript-Aufruf, sonst Timeout) → `{aufrufe, angesehen, weggewischt, likes, avd}`
   - `shorts.py perf <ID> aufrufe=… angesehen=… weggewischt=… avd=… likes=…`
3. **Analysieren** (Gewinner vs. Verlierer vergleichen): Transkript-Anfang (erste 2 s!), Länge, Streamer, Inhalt (Talk vs. Gameplay), Headline-Stil, Design v1/v2, Uhrzeit, `experiment`.
   Gewinner = viele Aufrufe/Std UND angesehen ≥ 55 %. Verlierer = < 10 Aufrufe nach 24 h oder angesehen < 45 %.
4. **`STRATEGIE.md` aktualisieren**, wenn es neue Belege gibt: Regel mit konkretem Beleg (Video, Zahlen) ergänzen/ändern/streichen, Experiment-Tabelle pflegen, eine Zeile ins „Log der Analysen“. Nur Aussagen mit Daten-Beleg als Regel; Vermutungen als Hypothese/Experiment.
5. Fertige, noch nicht gepostete Shorts gegen die aktuellen Regeln prüfen – passt einer nicht mehr (z. B. schwacher Einstieg, zu lang), neu schneiden oder `skip` setzen.

## Teil B – Nächsten Clip suchen (direkt nach Teil C)

**Zuerst `STRATEGIE.md` lesen** – die Regeln dort haben Vorrang vor den allgemeinen Kriterien unten. Bei jedem Pick bewusst eine Strategie-Regel anwenden und, wenn sinnvoll, ein offenes Experiment testen: im Pick `"experiment": "<was getestet wird>"` eintragen.


Ziel: Es sollen immer **2 fertige, ungepostete** Shorts bereitliegen. Fertige Shorts, die älter als 36 Stunden sind (Datum im Ordnernamen bzw. `uploaded` fehlt), nicht mehr posten → in ihrer .json `"skip": "zu alt"` setzen.

1. `shorts.py scout --channel kanal1 --range 24hr --limit 8` (neue Clips der letzten 24 h, schon gesehene werden übersprungen). Zu wenig Gutes → zusätzlich `--range 7d --limit 5`, aber Neues bevorzugen.
2. `scout\<datum>.txt` lesen (nur Abschnitt StreamerclipsDE) und **kritisch** auswählen:
   - lustig/spannend **und ohne Vorwissen verständlich**
   - **die Pointe/Auflösung muss im Clip sein** – endet der Clip vor der Antwort/Reaktion, NICHT nehmen
   - keine Werbung/Sponsor-Reads, keine Wett-/Casino-Seiten im Bild, keine Musik-Hauptinhalte
   - kein Clip, der schon gepostet wurde oder fast gleich ist (gleicher Moment aus anderem Clip)
3. Auswahl in `picks\<datum>_<HHMM>.json`: `[{"id": "...", "headline": "kurz, max ~45 Zeichen, mit Emoji", "title": "YouTube-Titel", "start": s, "end": s}]` (start/end optional – schneide Leerlauf am Anfang weg, aber nie die Pointe am Ende).
4. `shorts.py render picks\<datei>.json`
5. **Ansehen und prüfen:** `shorts.py sheet "<mp4>"` → PNG mit Read anschauen. Prüfen:
   - Gesicht nicht vom Banner verdeckt, Banner gut lesbar, keine doppelten Untertitel (eingebrannte Stream-Untertitel), Layout passt (Facecam oben / Gameplay unten bzw. Vollbild)
   - Untertitel-Text in der .json/.ass ergibt Sinn
   - Nicht gut? → neu schneiden (start/end anpassen, neu rendern) oder in der .json `"skip": "<Grund>"` setzen und den nächsten Kandidaten nehmen.

## Regeln
- Nur auf StreamerclipsDE posten. Keine anderen Kanäle, keine Kanal-Einstellungen ändern, keine Videos löschen oder bearbeiten.
- Keine Änderungen an `shorts.py`, `config.toml`, `studio_upload.js`.
- Kein API-Upload (`shorts.py upload`), nur Browser.
- Chrome nicht verbunden → nicht posten, aber Teil B trotzdem machen; im Bericht melden.
- Am Ende eine Zeile an `logs\posting.log` anhängen: `<Zeit> | gepostet: <Titel> <ID oder -> | bereit: <Anzahl> | Notiz`.
