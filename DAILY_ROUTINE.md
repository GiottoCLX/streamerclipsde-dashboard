# Tägliche Routine (wird jeden Tag automatisch von Claude ausgeführt)

Ordner: `C:\Users\diene\Desktop\Shorts Automatik`
Python immer über `.\.venv\Scripts\python.exe` aufrufen (PowerShell, im Projektordner).
Kanal: StreamerclipsDE (`kanal1`, Login liegt in `tokens/kanal1.json`).

## 1. Kandidaten holen

```powershell
.\.venv\Scripts\python.exe shorts.py scout --range 7d --limit 20
```
Dauert ca. 10–15 Minuten (im Hintergrund laufen lassen). Ergebnis: `scout/<heute>.txt` mit Transkripten der neuen Clips.

## 2. Die besten Clips auswählen (Ziel: 6 Videos pro Tag)

`scout/<heute>.txt` komplett lesen. Ein Clip ist gut, wenn:
- er **ohne Vorwissen verständlich** ist (mit einer kurzen Überschrift als Kontext),
- er **lustig oder spannend** ist: Rant, Reaktion, Pointe, absurde Aussage, Streit,
- genug Sprache drin ist (nicht nur Gameplay-Geräusche, kein reines Englisch aus dem Spiel).

Aussortieren:
- Werbung / Rabattcodes / Sponsoring, Ankündigungen, Giveaways
- Clips, die fast nur aus Beleidigungen bestehen, sexuelle oder hasserfüllte Inhalte, Drama über Privatpersonen
- Clips, deren Witz nur mit Bild funktioniert und im Transkript nicht erkennbar ist
- Überschriften dürfen nichts behaupten, was im Clip nicht passiert (nichts Irreführendes über echte Personen)

Ziel sind **6 Uploads pro Tag**. Zuerst zählen, wie viele fertige, noch nicht hochgeladene Shorts schon in output/*/ liegen (.json mit uploaded = false und ohne skip). Dann so viele neue Clips auswählen, dass es mindestens 6 sind (gern 1–2 mehr als Reserve).
Wenn möglich verschiedene Streamer mischen. Qualität geht vor Menge: Wenn nicht genug gute Clips da sind, lieber weniger nehmen und das in der Zusammenfassung sagen.

Auswahl schreiben nach `picks/<heute>.json`:
```json
[
  {"id": "3092785643",
   "headline": "Trymacs rastet wegen Willis Sound-Setup aus 😂",
   "title": "Trymacs: „Das schlechteste Soundsetup von ganz Twitch-Deutschland“ 😂",
   "start": 0.0, "end": 57.0}
]
```
- `headline`: kurz (max. ~50 Zeichen), wird oben im Video eingeblendet und gibt Kontext
- `title`: YouTube-Titel, neugierig machend, mit Streamer-Name
- `start`/`end` (optional, Sekunden): langweilige Anfänge/Enden wegschneiden, laut Zeitstempeln im Transkript

## 3. Rendern

```powershell
.\.venv\Scripts\python.exe shorts.py render picks\<heute>.json
```

## 4. Kontrolle

Von jedem neuen Video (`output/<heute>/*.mp4`) ein Standbild bei ca. 10 s ziehen und ansehen (ffmpeg liegt unter `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe`):
- Facecam oben / Gameplay unten bzw. Streamer sichtbar, Überschrift lesbar, Untertitel vorhanden
- Ist ein Video kaputt oder schlecht: in seiner `.json` `"skip": true` setzen, damit es nicht hochgeladen wird

## 5. Hochladen

```powershell
.\.venv\Scripts\python.exe shorts.py upload --schedule
```
Lädt bis zu 6 Videos hoch und plant sie auf 11:00 / 13:00 / 15:00 / 17:00 / 19:00 / 21:00 (bis dahin privat, dann automatisch öffentlich). Ältere, noch nicht hochgeladene Shorts kommen zuerst dran.
Nach dem Upload prüfen (z.B. per API videos.list mit part=status): Wenn YouTube ein Video als gesperrt/abgelehnt markiert (`uploadStatus` = rejected oder Hinweis auf Sperre), in der Zusammenfassung deutlich melden.
Bei `quotaExceeded`: einfach aufhören, am nächsten Tag geht es weiter. (6 Uploads = 9.600 von 10.000 Quota-Punkten pro Tag – nicht mehr als 6 Uploads versuchen.)

## 6. Abschluss

Kurze Zusammenfassung auf Deutsch: welche Clips ausgewählt wurden (Streamer + Überschrift), welche hochgeladen wurden (Links), Fehler oder Auffälligkeiten.
Fehlermeldungen niemals einfach ignorieren, sondern in der Zusammenfassung nennen.
