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

## Vorschläge für REGELN.md
Claude ändert REGELN.md nicht selbst. Wenn die Zahlen eine Regeländerung nahelegen, steht der Vorschlag hier (mit Beleg) – der Nutzer entscheidet.
- (noch keine)

## Log der Analysen
- **25.11.2026 16:50** – erste Auswertung (9 Shorts). 3 Gewinner (608/335/292 Aufrufe) alle aus dem 12-Uhr-Batch, Layout v1, Talk/Aussage-Clips. 2 Shorts im Test durchgefallen (80–100 % weggewischt) – beide mit schwachem Einstieg. Neue v2-Shorts (Pyramide, Krabbe, Krokodil, Niklas) noch zu jung für ein Urteil.
- **25.11.2026 18:10** – (keine Studio-Abfrage fällig, letzte 16:50). API: Gewinner wachsen weiter (Armut 612 / 108 pro Std, Bauprojekt 365, Soundsetup 214). Alle v2-Shorts 0–3 Aufrufe → werden kaum getestet (siehe Experiment Design). Gepostet: Trymacs Stinger/Angel (20,8 s, Einstieg „Oh mein Gott, nein!“) als Test „kurz + starker Einstieg“. Pyramide Teil 2 und Trymacs Tierleichen (Einstieg „Ich geh ja gleich mal rüber…“) wegen Regel 2 aussortiert.
- **25.11.2026 20:12** – Studio: Krokodil 4 Aufrufe/100 % angesehen, Stinger 3/100 % (je 0 weggewischt). API: Armut 998 (130/Std), Bauprojekt 489, Soundsetup 321; alle 7 Shorts seit dem 12-Uhr-Batch bei 0–7 Aufrufen. Folgerung: Problem ist die Ausspielung, nicht Einstieg/Inhalt (Regel 2 trotzdem weiter anwenden). Gepostet: Monte GTA6-Real-Life (Talk/Zitat). Neu gerendert: Monte „Gerechte Strafe“ (GTA, Schreckmoment-Einstieg, 21 s) und Monte „Einfach machen? Das ist gelogen“ (Talk, Frage-Einstieg, 38 s).
