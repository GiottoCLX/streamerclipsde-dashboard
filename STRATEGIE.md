# Reichweiten-Strategie StreamerclipsDE

Lebendes Dokument: Wird bei jeder Analyse aktualisiert. **Vor jeder Clip-Auswahl lesen und die Regeln anwenden.**
Daten: `shorts.py stats` (Aufrufe/Likes über API) + Studio-Werte pro Short (`perf`: angesehen %, weggewischt %, avd = Ø Sekunden).

## Wie YouTube Shorts verteilt (Arbeitsmodell)
- Jeder neue Short wird erst einer kleinen Testgruppe gezeigt. Entscheidend ist **„Angesehen vs. weggewischt“**: Wer in den ersten 1–2 Sekunden wegwischt, killt den Short.
  Danach zählt, **wie viel vom Video** angesehen wird (Ø Wiedergabedauer ÷ Länge) und ob Leute es mehrfach ansehen (Loops).
- Richtwerte: angesehen **≥ 70 %** = stark, 55–70 % = okay, < 50 % = schwach. Ø Wiedergabe ≥ 70 % der Länge = stark.
- Ein Short mit < 10 Aufrufen nach 24 h ist im Test durchgefallen (YouTube zeigt ihn kaum noch).

## Aktuelle Regeln (aus den Daten abgeleitet – mit Beleg)
1. **Starkes Zitat / klare Aussage gewinnt.** Bestes Video: „Eure Armut kotzt mich an“ – Monte (608 Aufrufe, 60 % angesehen, 18 Likes = 3 %). Kontroverse, wörtlich zitierte Aussage im Titel + Banner.
   → Titel und Headline möglichst als **wörtliches, provokantes Zitat in „…“** formulieren.
2. **Die ersten 2 Sekunden müssen sitzen und zur Headline passen.** Im Test zu 80–100 % weggewischt (3 Aufrufe):
   „Monte rastet wegen Stream-Sound aus“ – beginnt mit „Ne, brauchst du nicht mehr. Mach mal morgen Termin bei Arbeitsamt…“ (ohne Kontext unverständlich, passt nicht zur Headline);
   „Monte verprügelt Schradin“ – beginnt mit „Okay, nein. Ganz kurz.“ (Leerlauf, man muss Schradin kennen).
   Gewinner „Eure Armut…“ beginnt mit einer klaren Frage: „Wie war Neuseeland? Ich sage euch, wie Neuseeland war.“
   → Clip **dort starten, wo der erste Satz allein Neugier weckt** (Frage, krasse Aussage, Schreckmoment). Kein Begrüßen, keine Sub-Danksagungen, kein „Okay, warte“.
   → Keine Clips, die Insider-Wissen über Nebenpersonen brauchen.
3. **Kürzer ist besser (Hypothese, n klein).** 60-s-Clips halten nur ~15–19 s Ø (25–33 %). Trymacs Soundsetup (60 s) wurde zu 62 % weggewischt.
   → Ziel **15–35 s**. Lange Clips mit start/end auf den Kern schneiden.
4. **Pointe muss drin sein** (Nutzer-Feedback 25.11.: Pyramiden-Clip endete ohne Auflösung).
5. **Einzeln posten, regelmäßig** (seit 25.11. alle 2 h) – vorher wurden 6 auf einmal hochgeladen.
6. **Kein Zoom-Effekt, Gesicht immer komplett** (Nutzer-Vorgabe 25.11. 21:00: „der Zoom ist voll Arsch“, Köpfe oben oft abgeschnitten).
   Seit 21:05 im Code: kein Ruck-Zoom mehr bei lauten Stellen; Facecam-Fläche passt sich der Cam an (620–920 px hoch), Kopf mit Luft nach oben, abgeschnitten wird nur unten (Brust/Mikro); würde das Gesicht angeschnitten, wird die ganze Cam gezeigt (Seiten unscharf).
   → Beim Sheet-Check prüfen: Kopf/Mütze oben vollständig, Mund/Kinn sichtbar.

## Offene Experimente (immer nur 1 Variable ändern, im Pick als `"experiment"` vermerken)
| Experiment | Variante | Status |
|---|---|---|
| Länge | ≤ 30 s vs. 45–60 s | läuft – ab jetzt bevorzugt kurz, Vergleich mit den 60-s-Clips |
| Inhalt | Just Chatting / Aussage vs. GTA-Gameplay | läuft – GTA-Clips vom 25.11. (Krabbe, Krokodil) beobachten |
| Headline-Stil | wörtliches Zitat „…“ vs. Beschreibung („Monte trifft auf…“) | läuft |
| Design | v1 (altes Layout) vs. v2 (neues Layout) | **Warnsignal 18:10:** alle 4 v2-Shorts bekommen kaum Impressionen (Niklas 2 Aufrufe nach 5,7 h – im selben Batch wie die 3 v1-Gewinner; Pyramide 3, Krabbe 1 nach 3,4 h; Krokodil 0 nach 1,6 h). Nicht weggewischt, sondern gar nicht ausgespielt. Design ist im Code an den Pfad gekoppelt (`design` aus `kanal` im Dateinamen) → nicht per Pick testbar, Nutzer informieren. Urteil nach 24 h. **20:12:** Muster hält (n=6): Stinger (starker Einstieg, 100 % angesehen) nur 3 Aufrufe nach 2 h, Krokodil 4 nach 3,6 h – die wenigen Zuschauer schauen also zu Ende, es fehlt nur die Ausspielung. Gleichzeitig wachsen die v1-Shorts weiter (Armut 998, +130/Std) → Kanal ist nicht generell gedrosselt. Starker Hinweis auf v2-Layout (oder Upload-Weg/-Datei), aber noch nicht bewiesen. |
| Layout v3 | ohne Zoom + angepasste Facecam (ab 25.11. 21:05, erster: Trymacs Vogel EazTuqIluFY) vs. v2 | läuft – Ausspielung (Aufrufe nach 2–24 h) mit den v2-Shorts vergleichen |
| Teil-2-Clips | Fortsetzung eines geflopten Clips | nicht mehr machen – „Teil 2“ braucht Vorwissen (Regel 2), Pyramide Teil 2 am 25.11. 18:10 auf skip |

## Stream Clips Daily (englisch, kanal4) – eigene Notizen
Start 25.11.2026. Noch keine eigenen Zahlen; die deutschen Regeln oben gelten als Startannahme, bis eigene Belege da sind.
- Beobachtung 25.11.: Viele Clips von Kai Cenat und Jynxzi kommen schon im Hochformat mit eingebrannten Untertiteln → `"subtitles": false` oder Clip meiden (doppelte Untertitel).
- Beobachtung 25.11.: Frische 24-h-Clips sind oft GTA-Chaos ohne klaren Moment; die Top-Clips der Woche (meiste Aufrufe) sind eher Highlights.
- Hypothese: US-Publikum ist abends deutscher Zeit (ab ~15 Uhr) aktiv → Posts nachmittags/abends sollten besser laufen. Prüfen, sobald Zahlen da sind.

## Vorschläge für REGELN.md
Claude ändert REGELN.md nicht selbst. Wenn die Zahlen eine Regeländerung nahelegen, steht der Vorschlag hier (mit Beleg) – der Nutzer entscheidet.
- **Kanal-Wechsel als fester Schritt (26.11. 06:10):** Die Studio-Fehler („Hoppla/nicht berechtigt“, 22:10–04:10) kamen daher, dass im Browser der andere Kanal (Stream Clips Daily) aktiv war. Beide Kanäle liegen im selben Google-Konto; über `https://www.youtube.com/channel_switcher` lässt sich ohne Login auf StreamerclipsDE umschalten – danach liefen die Studio-Analysen sofort. Vorschlag: in REGELN.md Abschnitt 5/7 festhalten, dass jeder Lauf vor dem Upload per Kanal-Wechsler auf seinen Kanal umschaltet (die zwei Läufe schalten sich sonst gegenseitig weg).

- **Upload-Limit (26.11. 08:10):** Studio meldet für StreamerclipsDE „Tägliches Upload-Limit erreicht“ – erst nach Identitätsbestätigung (nur der Nutzer) gehen mehr Uploads pro Tag. Vorschlag: Nutzer bestätigt die Identität in Studio; in REGELN.md Abschnitt 7 ergänzen: „Upload-Limit-Meldung → nicht posten, Warnung, nächster Versuch frühestens nach 24 h“.

## Log der Analysen
- **25.11.2026 16:50** – erste Auswertung (9 Shorts). 3 Gewinner (608/335/292 Aufrufe) alle aus dem 12-Uhr-Batch, Layout v1, Talk/Aussage-Clips. 2 Shorts im Test durchgefallen (80–100 % weggewischt) – beide mit schwachem Einstieg. Neue v2-Shorts (Pyramide, Krabbe, Krokodil, Niklas) noch zu jung für ein Urteil.
- **25.11.2026 18:10** – (keine Studio-Abfrage fällig, letzte 16:50). API: Gewinner wachsen weiter (Armut 612 / 108 pro Std, Bauprojekt 365, Soundsetup 214). Alle v2-Shorts 0–3 Aufrufe → werden kaum getestet (siehe Experiment Design). Gepostet: Trymacs Stinger/Angel (20,8 s, Einstieg „Oh mein Gott, nein!“) als Test „kurz + starker Einstieg“. Pyramide Teil 2 und Trymacs Tierleichen (Einstieg „Ich geh ja gleich mal rüber…“) wegen Regel 2 aussortiert.
- **25.11.2026 20:12** – Studio: Krokodil 4 Aufrufe/100 % angesehen, Stinger 3/100 % (je 0 weggewischt). API: Armut 998 (130/Std), Bauprojekt 489, Soundsetup 321; alle 7 Shorts seit dem 12-Uhr-Batch bei 0–7 Aufrufen. Folgerung: Problem ist die Ausspielung, nicht Einstieg/Inhalt (Regel 2 trotzdem weiter anwenden). Gepostet: Monte GTA6-Real-Life (Talk/Zitat). Neu gerendert: Monte „Gerechte Strafe“ (GTA, Schreckmoment-Einstieg, 21 s) und Monte „Einfach machen? Das ist gelogen“ (Talk, Frage-Einstieg, 38 s).
- **25.11.2026 22:10** – Kein Post (Mindestabstand: letzter Post vor 64 Min.). API: Armut 1392 (144/Std, beschleunigt weiter), Bauprojekt 489, Soundsetup 343. Alle 9 Shorts seit dem 12-Uhr-Batch weiter bei 0–8 Aufrufen, auch GTA6-Real-Life (4 nach 2 h) und der erste v3-Short Tierleiche (0 nach 1,1 h) → Ausspielungsproblem besteht auch mit Layout v3 (noch jung, Urteil morgen). Studio-Abfrage fiel aus (Studio zeigt für StreamerclipsDE „Hoppla“ – vermutlich anderer Kanal im Browser aktiv). Vorbereitung: Monte „Apfel“ nach Sheet aussortiert (Pointe/Schüsse nicht im Bild), Trymacs Jumpscare = gleiche Krokodil-Szene wie gepostet → aussortiert. Vorrat 1.
- **26.11.2026 00:10** – Kein Post (außerhalb 06–24 Uhr). API seit 22:10: Armut 1392 → 1396 (Wachstum praktisch gestoppt nach ~12 h), Bauprojekt 489 → 596 (+107, zieht nach), Soundsetup 343 (Stillstand). Alle 9 Shorts seit dem 12-Uhr-Batch weiter 0–8 Aufrufe; erster v3-Short Tierleiche 0 nach 3,1 h → Ausspielungsproblem besteht mit v3 unverändert. Studio-Analytics wieder „Ein Fehler ist aufgetreten“ (2. Lauf in Folge) → keine Studio-Werte. Vorbereitung: 24 h + 7 Tage gesichtet (42 Kandidaten), kein Clip mit Note 8+ (Monte Dom-Story endet vor der Pointe; „Geld nur durch Kinder“ wirrer Einstieg + Beleidigung am Ende, ≈6–7; Drachenlord braucht Vorwissen/bloßstellend). Vorrat 1 (Trymacs Festival, Note 8).
- **26.11.2026 02:10** – Kein Post (außerhalb 06–24 Uhr). API seit 00:10: Armut 1396 → 1424 (+28 in 2 h, ausgelaufen), Bauprojekt 596 → 599 (Stillstand), Soundsetup 343 → 354. Alle 9 Shorts seit dem 12-Uhr-Batch weiter 3–8 Aufrufe (Tierleiche 3 nach 5,1 h, GTA6-Real-Life 5 nach 6 h) → Ausspielungsproblem unverändert, betrifft v2 und v3 gleich. Studio: „Nicht berechtigt“ für StreamerclipsDE → im Browser ist ein anderes Konto aktiv (erklärt auch die Fehler 22:10/00:10). Vorbereitung: 24 h + 7 Tage (72 Kandidaten) – kein 8+ (Heli-Abschuss nur GTA-Chaos + Beleidigung, Synchro-Clip enthält Gönrgy-Werbung, Rest Gelaber/Insider). Vorrat 1 (Trymacs Festival).
- **26.11.2026 04:10** – Kein Post (außerhalb 06–24 Uhr). API seit 02:10: Armut 1424 (Stillstand), Bauprojekt 599, Soundsetup 356; alle 9 Shorts seit dem 12-Uhr-Batch weiter 3–9 Aufrufe (Tierleiche 3 nach 7,1 h, GTA6-Real-Life 5 nach 8 h) → Ausspielungsproblem unverändert. Studio wieder „Ein Fehler ist aufgetreten“ (falsches Konto im Browser, 4. Lauf in Folge) → keine Studio-Werte. Vorbereitung: 24 h ohne 8+ (Eli „Lucia Red Flags“ enthält „Schlampe“, Strip-Club-Telefon ≈6); 7 Tage mit 12 Clips/Streamer (123 Kandidaten) → Monte „Polizei macht nichts“ (GTA 6, wird neben Polizist verprügelt, Bulle läuft weg; 33 s, Note 8) geschnitten. Monte Krokodil-Füttern verworfen (zu ähnlich zum geposteten Krokodil-Short). Vorrat 2.
- **26.11.2026 06:10** – Kein Post: Studio zeigte erst den falschen Kanal (per Kanal-Wechsler auf StreamerclipsDE umgeschaltet), danach blieb beim Upload von Trymacs Festival „Veröffentlichen“ gesperrt und es entstand kein Entwurf → nicht wiederholt. Studio-Werte erstmals seit 20:12 wieder: Armut 1432 Aufrufe, **65,5 % angesehen** (vorher 60,3), Ø 20,9 s von 56 s, 36 Likes (2,5 %); Bauprojekt 599, 60,6 % angesehen, Ø 15,6 s von 60 s; GTA6-Real-Life 5 Aufrufe/100 % angesehen; Tierleiche 2 Aufrufe/50 % weggewischt. Bestätigt: Die Gewinner halten gute Ansehen-Quoten, die neuen Shorts bekommen schlicht keine Ausspielung (2–9 Aufrufe nach 9–18 h). API: Armut 1429 (Stillstand), Bauprojekt 599, Soundsetup 356. Vorrat 2 (Trymacs Festival, Monte Polizei – beide Note 8, frisch).
- **26.11.2026 08:10** – Kein Post: Studio (richtiger Kanal StreamerclipsDE) zeigt nach dem Datei-Upload **„Tägliches Upload-Limit erreicht“** (Identitätsbestätigung oder 24 h warten) → erklärt vermutlich auch den gesperrten „Veröffentlichen“-Knopf um 06:10. Dialog geschlossen, kein Entwurf entstanden. Studio: Soundsetup 355 Aufrufe, 41,3 % angesehen (Ø 14,2 s von 60 s) – trotz schwacher Quote früh ausgespielt; Sound-Ausraster 11 Aufrufe/33 % angesehen, Schradin 8/20 %, Niklas 2/33 % → bestätigt Regel 2 (schwacher Einstieg = weggewischt). API: Armut 1431, Bauprojekt 599, Soundsetup 356 – alle drei Gewinner stehen; alle Shorts seit dem 12-Uhr-Batch 3–9 Aufrufe. Vorrat 2 (voll, beide Note 8), nichts Neues geschnitten.
