# Shorts-Automatik

Holt die meistgesehenen Twitch-Clips der Streamer aus `config.toml` und macht daraus fertige YouTube Shorts (1080x1920, mit Untertiteln, Titel und Beschreibung inkl. Credits).

## Benutzen

In PowerShell in diesem Ordner:

```powershell
.\.venv\Scripts\python.exe shorts.py check
```
zeigt die aktuellen Top-Clips pro Streamer.

### Mit Auswahl (beste Qualität)

```powershell
.\.venv\Scripts\python.exe shorts.py scout --range 30d --limit 12
```
lädt die Top-Clips, transkribiert sie und schreibt alles nach `scout/<datum>.txt`. Daraus werden die besten Momente ausgewählt und in `picks/<datum>.json` eingetragen (Clip-ID, Überschrift, Titel, optional `start`/`end` in Sekunden zum Kürzen):

```powershell
.\.venv\Scripts\python.exe shorts.py render picks\2026-11-25.json
```

### Vollautomatisch (ohne Auswahl)

```powershell
.\.venv\Scripts\python.exe shorts.py run
```
erstellt neue Shorts aus den Top-Clips für alle Streamer (Anzahl pro Streamer: `clips_per_streamer` in `config.toml`). Die Überschrift ist dann einfach der Twitch-Clip-Titel.

### Layout

Wird automatisch erkannt: Gameplay mit Facecam → Facecam oben, Gameplay unten. Streamer füllt das Bild → Zuschnitt auf den Streamer. Kein Gesicht → ganzes Bild mit unscharfem Hintergrund.

```powershell
.\.venv\Scripts\python.exe shorts.py run --streamer Trymacs --count 1
```
nur ein Streamer, nur ein Short.

## Ergebnis

- `output/<datum>/*.mp4`: das fertige Short
- `output/<datum>/*.json`: Titel, Beschreibung, Tags, Transkript (für den Upload)
- `state.json`: merkt sich, welche Clips schon verarbeitet wurden (nie doppelt)

## Anpassen

Alles in `config.toml`: Streamer hinzufügen/entfernen, Layout (`blur`, `center`, `split`), Zoom, Zeitraum, Hashtags, Untertitel-Modell.

## YouTube & Zeitplan

- Upload: siehe `YOUTUBE_SETUP.md` (Kanal StreamerclipsDE ist als `kanal1` verbunden)
- Täglich um ca. 10:05 Uhr führt Claude die Routine aus `DAILY_ROUTINE.md` aus (geplante Aufgabe „StreamerclipsDE: tägliche Shorts“ in der Claude-App). Die Claude-App muss dafür offen sein.

## Noch offen

- Highlights aus kompletten Streams (VODs) über Chat-Aktivität
- Kanal 2 und 3
