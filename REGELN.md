# Regeln für Claude – StreamerclipsDE & Stream Clips Daily

**Diese Datei ist die einzige verbindliche Anweisung.** Was hier steht, gilt – egal was in einem Chat besprochen wurde.
Jeder Lauf lädt zuerst die neueste Version von GitHub. Ändern: auf GitHub die Datei öffnen → Stift-Symbol → speichern.
Claude ändert diese Datei **nie von sich aus**, sondern schlägt Änderungen nur vor (im Bericht und im Dashboard unter „Vorschläge“).

Rangfolge bei Widersprüchen: **REGELN.md** (du) → `STRATEGIE.md` (Claudes Lern-Notizen aus den Zahlen) → `POSTING_ROUTINE.md` (Technik-Anleitung).

Alle Regeln ab Abschnitt 2 gelten für **beide Kanäle**. Nur die Schalter sind pro Kanal.

---

## 1. Schalter

Nur den Wert hinter dem Doppelpunkt ändern.

### StreamerclipsDE (kanal1)

Deutsch · @clx_visuals · Läufe zu jeder **geraden** Stunde (00, 02, 04 …)

- **Pause:** nein
- **Posts pro Lauf:** 1
- **Posting-Zeiten:** 06:00-24:00
- **Mindestabstand zwischen zwei Posts (Minuten):** 100
- **Fertige Shorts auf Vorrat:** 2
- **Cliplänge (Sekunden):** 15-45
- **Fertige Shorts verfallen nach (Stunden):** 36
- **Streamer:** eliasn97, sidneyeweka, niklaswilson, trymacs, montanablack88

### Stream Clips Daily (kanal4)

Englisch · @streamclipsdailyen · Läufe zu jeder **ungeraden** Stunde (01, 03, 05 …)

- **Pause:** nein
- **Posts pro Lauf:** 1
- **Posting-Zeiten:** 06:00-24:00
- **Mindestabstand zwischen zwei Posts (Minuten):** 100
- **Fertige Shorts auf Vorrat:** 2
- **Cliplänge (Sekunden):** 15-45
- **Fertige Shorts verfallen nach (Stunden):** 36
- **Streamer:** kaicenat, jynxzi, marlon, lacy, stableronaldo

Bedeutung:

- *Pause: ja* → nichts posten, nichts Neues schneiden. Es werden nur die Zahlen aktualisiert und das Dashboard gepflegt.
- *Posting-Zeiten* → außerhalb dieser Zeit wird nicht gepostet, aber trotzdem ausgewertet und der nächste Clip vorbereitet. (Deutsche Uhrzeit – beim englischen Kanal ist das US-Publikum 6–9 h zurück.)
- *Verfallen* → ein fertig geschnittener, aber noch nicht geposteter Short wird nach dieser Zeit aussortiert und nicht mehr gepostet, weil der Clip dann nicht mehr aktuell ist (Twitch-Momente sind nach 1–2 Tagen „alt“, oft haben ihn andere Kanäle schon gepostet).
- *Mindestabstand* → wurde vor kürzerer Zeit gepostet (z. B. manuell im Chat), wird in diesem Lauf nicht gepostet.
- *Streamer* → nur Clips dieser Twitch-Kanäle. Neuer Name hier → der nächste Lauf trägt ihn in `config.toml` ein (beim passenden Kanal).

Wie oft ein Lauf startet (derzeit **alle 2 Stunden pro Kanal**, versetzt um 1 Stunde, bis ~9 Min. später), ist in der Claude-App eingestellt – das kann diese Datei nicht ändern. Dafür Claude im Chat Bescheid sagen.

---

## 2. Ablauf jedes Laufs (genau in dieser Reihenfolge)

Jeder Schritt wird live im Dashboard gemeldet (`live.py step`).

1. **Start:** `live.py start --channel <kanal>` – neueste Regeln laden, Live-Status „läuft“.
2. **Prüfen:** `live.py check --channel <kanal>` – darf jetzt gepostet werden? (Pause, Posting-Zeiten, Mindestabstand). Ergebnis melden.
3. **Posten** (nur wenn erlaubt und ein geprüfter Short bereitliegt): ältester fertiger Short über YouTube Studio im Browser, öffentlich. Danach prüfen, dass er wirklich öffentlich ist.
4. **Zahlen auswerten:** Aufrufe aller Shorts holen, für junge Shorts (2–72 h) die Studio-Werte (angesehen/weggewischt). Gewinner und Verlierer vergleichen, Erkenntnisse in `STRATEGIE.md` (nur mit Zahlen-Beleg).
5. **Vorrat prüfen:** fertige Shorts gegen diese Regeln prüfen; zu alte oder unpassende aussortieren (mit Grund).
6. **Nächsten Clip vorbereiten**, bis der Vorrat (Schalter) wieder voll ist: neue Twitch-Clips der letzten 24 h suchen (sonst 7 Tage), auswählen, schneiden, Vorschaubild ansehen und kritisch prüfen.
7. **Abschluss:** Log-Zeile, Dashboard aktualisieren, `live.py done` mit kurzer Zusammenfassung, Bericht auf Deutsch.

Geht etwas schief: `live.py warn` (weiter machen) oder `live.py fail` (Lauf abbrechen) – mit Grund.

---

## 3. Welche Clips genommen werden

**Sehr streng prüfen. Lieber gar nichts posten als einen mittelmäßigen Short.** Nur echte Highlights: ein **lustiger** Moment (man lacht wirklich), ein **krasser** Moment (Schreck, Fail, Rage, unfassbare Situation) oder ein **cooler** Moment (Skill, epische Szene, legendäre Aussage). Kein Gelaber, keine Meinungen ohne Knall, kein „ganz nett“.

**Qualitäts-Check – jeder Punkt muss mit JA beantwortet werden:**

1. **Weiterschick-Test:** Würde man den Clip einem Freund schicken („guck mal 😂“)?
2. **Ein klarer Moment:** Lässt sich in einem Satz sagen, was passiert und warum es lustig/krass/cool ist?
3. **Sofort verständlich:** Versteht man in den ersten 3 Sekunden ohne Kontext, worum es geht?
4. **Der Moment ist komplett drin:** Entweder passiert er live im Bild – oder es ist eine **lustige Story, die im Clip vollständig erzählt wird** (Anfang, Pointe, Reaktion). Nicht ok: Momente, die nur im Nebensatz erwähnt werden oder bei denen man den Rest der Geschichte nicht mitbekommt. (Beispiel ok: Trymacs erzählt, wie Nici auf fremde Bühnen klettert und eine Faust von der Security kassiert.)
5. **Pointe drin:** Die Reaktion/Auflösung ist im Clip.
6. **Kein Leerlauf:** keine Pausen, kein Drumherum-Reden, kein Wirrwarr aus mehreren Leuten durcheinander.

Danach eine **Note von 1–10** vergeben (10 = viral-verdächtig). **Nur ab Note 8 wird geschnitten und gepostet.** Note und eine Begründung in einem Satz („warum ist das cool?“) stehen im Pick (`"note"`, `"warum"`) und werden im Dashboard angezeigt. Nach dem Schneiden das Vorschaubild noch einmal mit demselben Maßstab prüfen – wirkt es geschnitten schwächer, aussortieren.

Findet ein Lauf keinen Clip mit Note 8+: weiter suchen (7 Tage, mehr Clips pro Streamer). Gibt es dann immer noch keinen, **nichts vorbereiten** und das im Bericht sagen.

Außerdem:

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

- Nur auf diese zwei Kanäle, immer über **YouTube Studio im Browser**, öffentlich, „nicht für Kinder“:
  - **StreamerclipsDE** (@clx_visuals, Kanal-ID UC5wsIwWO9EMifAyY9oLyRrQ) – nur deutsche Clips, Titel/Überschrift/Untertitel auf Deutsch.
  - **Stream Clips Daily** (@streamclipsdailyen, Kanal-ID UCItdS5ca1wZv4FBEM_6IarQ) – nur englische Clips, Titel/Überschrift/Untertitel auf **Englisch**.
- Vor dem Upload prüfen: Studio zeigt den richtigen Kanal, Titel noch nicht in dessen Shorts-Liste (keine Doppel-Uploads), Clip gehört zu diesem Kanal.
- Titel = Überschrift + Streamer-Name, Beschreibung mit Link zum Streamer und Original-Clip, „Alle Rechte beim Streamer“ (englisch: „All rights belong to the streamer“).

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
