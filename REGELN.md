# Regeln für Claude – StreamerclipsDE

**Diese Datei ist die einzige verbindliche Anweisung.** Was hier steht, gilt – egal was in einem Chat besprochen wurde.
Jeder Lauf lädt zuerst die neueste Version von GitHub. Ändern: auf GitHub die Datei öffnen → Stift-Symbol → speichern.
Claude ändert diese Datei **nie von sich aus**, sondern schlägt Änderungen nur vor (im Bericht und im Dashboard unter „Vorschläge“).

Rangfolge bei Widersprüchen: **REGELN.md** (du) → `STRATEGIE.md` (Claudes Lern-Notizen aus den Zahlen) → `POSTING_ROUTINE.md` (Technik-Anleitung).

---

## 1. Schalter

Nur den Wert hinter dem Doppelpunkt ändern.

- **Pause:** nein
- **Posts pro Lauf:** 1
- **Posting-Zeiten:** 08:00-24:00
- **Mindestabstand zwischen zwei Posts (Minuten):** 100
- **Fertige Shorts auf Vorrat:** 2
- **Cliplänge (Sekunden):** 15-40
- **Fertige Shorts verfallen nach (Stunden):** 36
- **Streamer:** eliasn97, sidneyeweka, niklaswilson, trymacs, montanablack88

Bedeutung:

- *Pause: ja* → nichts posten, nichts Neues schneiden. Es werden nur die Zahlen aktualisiert und das Dashboard gepflegt.
- *Posting-Zeiten* → außerhalb dieser Zeit wird nicht gepostet, aber trotzdem ausgewertet und der nächste Clip vorbereitet.
- *Mindestabstand* → wurde vor kürzerer Zeit gepostet (z. B. manuell im Chat), wird in diesem Lauf nicht gepostet.
- *Streamer* → nur Clips dieser Twitch-Kanäle. Neuer Name hier → der nächste Lauf trägt ihn in `config.toml` ein (Kanal kanal1).

Wie oft ein Lauf startet (derzeit **alle 2 Stunden zur vollen Stunde**, bis ~9 Min. später), ist in der Claude-App eingestellt – das kann diese Datei nicht ändern. Dafür Claude im Chat Bescheid sagen.

---

## 2. Ablauf jedes Laufs (genau in dieser Reihenfolge)

Jeder Schritt wird live im Dashboard gemeldet (`live.py step`).

1. **Start:** `live.py start` – neueste Regeln laden, Live-Status „läuft“.
2. **Prüfen:** `live.py check` – darf jetzt gepostet werden? (Pause, Posting-Zeiten, Mindestabstand). Ergebnis melden.
3. **Posten** (nur wenn erlaubt und ein geprüfter Short bereitliegt): ältester fertiger Short über YouTube Studio im Browser, öffentlich. Danach prüfen, dass er wirklich öffentlich ist.
4. **Zahlen auswerten:** Aufrufe aller Shorts holen, für junge Shorts (2–72 h) die Studio-Werte (angesehen/weggewischt). Gewinner und Verlierer vergleichen, Erkenntnisse in `STRATEGIE.md` (nur mit Zahlen-Beleg).
5. **Vorrat prüfen:** fertige Shorts gegen diese Regeln prüfen; zu alte oder unpassende aussortieren (mit Grund).
6. **Nächsten Clip vorbereiten**, bis der Vorrat (Schalter) wieder voll ist: neue Twitch-Clips der letzten 24 h suchen (sonst 7 Tage), auswählen, schneiden, Vorschaubild ansehen und kritisch prüfen.
7. **Abschluss:** Log-Zeile, Dashboard aktualisieren, `live.py done` mit kurzer Zusammenfassung, Bericht auf Deutsch.

Geht etwas schief: `live.py warn` (weiter machen) oder `live.py fail` (Lauf abbrechen) – mit Grund.

---

## 3. Welche Clips genommen werden

- Lustig oder spannend **und ohne Vorwissen verständlich** (keine Insider, keine „Teil 2“-Clips).
- **Der erste Satz weckt allein Neugier** – Frage, krasse Aussage, Schreckmoment. Kein Begrüßen, kein „Okay, warte“, kein Leerlauf am Anfang.
- **Die Pointe / Auflösung muss im Clip sein.** Endet der Clip vor der Antwort oder Reaktion → nicht nehmen.
- Frisch: bevorzugt Clips von heute/gestern.
- Nicht schon gepostet und nicht fast gleich wie ein geposteter Clip.
- **Verboten:** Werbung/Sponsor-Teile, Wett-/Casino-Seiten im Bild, Musik als Hauptinhalt, Clips, die jemanden bloßstellen oder beleidigen sollen.

## 4. Wie geschnitten wird

- **Kein Zoom-Effekt.**
- **Gesicht in der Facecam immer komplett:** Kopf/Mütze oben nicht abgeschnitten, Mund/Kinn sichtbar.
- Facecam oben, Gameplay unten; bei Just Chatting Zuschnitt auf den Streamer.
- Untertitel groß in der Mitte, Überschrift (Banner) als wörtliches Zitat oder klare Aussage, max. ~45 Zeichen, mit Emoji.
- Leerlauf am Anfang wegschneiden, aber **nie** die Pointe am Ende.
- Jeder Short wird vor dem Posten als Vorschaubild angesehen. Passt etwas nicht → neu schneiden oder aussortieren.

## 5. Posten

- Nur auf **StreamerclipsDE** (@clx_visuals, Kanal-ID UC5wsIwWO9EMifAyY9oLyRrQ), immer über **YouTube Studio im Browser**, öffentlich, „nicht für Kinder“.
- Vor dem Upload prüfen: richtiger Kanal eingeloggt, Titel noch nicht in der Shorts-Liste (keine Doppel-Uploads).
- Titel = Überschrift + Streamer-Name, Beschreibung mit Link zum Streamer und Original-Clip, „Alle Rechte beim Streamer“.

## 6. Was Claude nie tut

- Keine Videos löschen, auf privat stellen oder nachträglich bearbeiten – das entscheidest du.
- Keine Kanal-Einstellungen ändern, keine anderen Kanäle anfassen.
- Keine Passwörter eingeben, keine Logins oder Konto-Bestätigungen – das machst du.
- Kein API-Upload, nur Browser.
- Diese Datei (`REGELN.md`) nicht selbst ändern.
- Das Repo ist öffentlich: nie `client_secret.json`, Tokens, `state.json` oder Videos hochladen, `.gitignore` nicht ändern.
- Programmdateien (`shorts.py`, `dashboard.py`, `live.py`, `studio_upload.js`, `config.toml`) nur ändern, wenn du es im Chat ausdrücklich willst (Ausnahme: neuer Streamer aus Abschnitt 1 in `config.toml`).

## 7. Wenn etwas nicht geht

- Chrome nicht verbunden oder Studio nicht eingeloggt → **nicht posten**, Rest des Laufs trotzdem machen, Warnung im Dashboard.
- Upload abgelehnt / Fehler → nicht wiederholen, Warnung im Dashboard und im Bericht.
- Kein guter Clip gefunden → lieber **nichts** vorbereiten als einen schlechten Clip; im Bericht sagen.
