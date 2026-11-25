# YouTube-Upload einrichten (einmalig, ca. 10 Minuten)

Damit das Programm Videos auf deinen Kanal hochladen darf, brauchst du ein kostenloses Google-Cloud-Projekt.
Am Ende hast du eine Datei `client_secret.json`, die in diesen Ordner kommt.

> Melde dich überall mit dem Google-Konto an, dem der YouTube-Kanal gehört.

## 1. Projekt anlegen

1. Öffne https://console.cloud.google.com
2. Oben links auf die Projektauswahl klicken → **Neues Projekt**
3. Name: `Shorts Automatik` → **Erstellen**, dann das Projekt oben auswählen

## 2. YouTube-API aktivieren

1. Öffne https://console.cloud.google.com/apis/library/youtube.googleapis.com
2. Auf **Aktivieren** klicken

## 3. Zustimmungsbildschirm (OAuth) einrichten

1. Öffne https://console.cloud.google.com/auth/overview → **Jetzt starten**
2. **App-Informationen:** App-Name `Shorts Automatik`, Support-E-Mail = deine Adresse → Weiter
3. **Zielgruppe:** **Extern** → Weiter
4. **Kontaktdaten:** deine E-Mail → Weiter → Richtlinie akzeptieren → **Erstellen**
5. Links auf **Zielgruppe** → unter *Testnutzer* **Add users** → deine Google-Adresse eintragen → Speichern
6. Ebenfalls unter **Zielgruppe**: **App veröffentlichen** → bestätigen
   (Sonst läuft die Anmeldung alle 7 Tage ab. Die App wird dadurch nicht öffentlich, nur du benutzt sie.)

## 4. Zugangsdatei erstellen

1. Links auf **Clients** → **Client erstellen**
2. Anwendungstyp: **Desktop-App**, Name: `Shorts Automatik` → **Erstellen**
3. Im Fenster auf **JSON herunterladen**
4. Die Datei in diesen Ordner (`Desktop\Shorts Automatik`) legen und in **`client_secret.json`** umbenennen

Diese Datei ist wie ein Passwort: nicht teilen.

## 5. Kanal verbinden

In PowerShell in diesem Ordner:

```powershell
.\.venv\Scripts\python.exe shorts.py auth
```

Es öffnet sich der Browser:
- Google-Konto auswählen und, falls gefragt, den **richtigen YouTube-Kanal** auswählen
- Warnung „Google hat diese App nicht überprüft“ → **Erweitert** → **Weiter zu Shorts Automatik**
  (das ist normal, es ist deine eigene App)
- Zugriff erlauben

Für weitere Kanäle später: `shorts.py auth --channel kanal2` usw.

## 6. Hochladen

```powershell
.\.venv\Scripts\python.exe shorts.py upload
```
lädt bis zu 3 fertige Shorts hoch (Einstellung `privacy` in `config.toml`, Standard: privat).

```powershell
.\.venv\Scripts\python.exe shorts.py upload --schedule
```
verteilt die Videos auf die Zeiten in `publish_times` (12:00, 17:00, 20:00) und YouTube veröffentlicht sie automatisch.

## Öffentlich hochladen

YouTube kann Uploads von neuen, nicht geprüften API-Projekten auf **privat** sperren.
Bei diesem Projekt ist das **nicht** der Fall (getestet am 25.11.2026: ein per API hochgeladenes Video ließ sich öffentlich schalten).
Sollte YouTube Uploads später doch als „gesperrt (privat)“ markieren, hilft die kostenlose Prüfung:

- Formular: https://support.google.com/youtube/contact/yt_api_form → *YouTube API Services – Audit and Quota Extension*
- Dauert meist einige Tage bis wenige Wochen.

## Limits

- Pro Google-Projekt ca. **6 Uploads pro Tag** (10.000 Quota-Punkte, ein Upload kostet 1.600).
- Für 3 Kanäle mit mehr Uploads: pro Kanal ein eigenes Projekt, oder im Prüfformular mehr Quota beantragen.
