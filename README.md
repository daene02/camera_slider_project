# Camera Slider Project

Dieses Projekt ist eine umfassende Software- und Hardware-Lösung für einen motorisierten Kamera-Slider. Ziel ist es, präzise Kamerabewegungen zu ermöglichen, die für Film- und Fotoproduktionen unverzichtbar sind.

## Inhaltsverzeichnis

1. Überblick
2. Hardware-Komponenten
3. Software-Struktur
4. Funktionsumfang
5. Installation
6. Konfiguration
7. Bedienungsanleitung
8. Zukünftige Schritte

---

## 1. Überblick

In diesem Projekt wird ein Raspberry Pi in Kombination mit Dynamixel-Servomotoren eingesetzt, um eine zuverlässige, reproduzierbare und flexibel steuerbare Slider-Lösung anzubieten. Neben dem Sliden (lineare Bewegung) können damit auch Drehbewegungen (Pan/Tilt/Turntable), Zoom- und Fokusregler automatisiert werden. 

### Hauptziele

- Präzise und wiederholbare Kamerabewegungen
- Fernsteuerbarkeit über eine Weboberfläche
- Unterstützung mehrerer Achsen (z.B. Slider, Turntable, Fokus, Zoom, Pan, Tilt)
- Einfache Anpassung und Erweiterung dank modularer Architektur

---

## 2. Hardware-Komponenten

- ### Raspberry Pi
  Als zentrales Steuergerät, auf dem die Software läuft und der die Motoren ansteuert.

- ### Dynamixel-Servomotoren
  (X-Serie Protocol 2.0). Diese bieten eine präzise Positionierung und Feedback-Möglichkeiten über Strom, Spannung, Temperatur etc.

- ### Spannungsversorgung
  Zur Versorgung der Dynamixel-Motoren und des Raspberry Pi (je nach Motor-Typ und Anzahl können hier unterschiedliche Anforderungen bestehen).

- ### Schlittenführung (Slider)
  Mechanische Schiene zum linearen Bewegen der Kamera.

- ### Drehteller (Turntable)
  Ermöglicht Rundum-Aufnahmen oder horizontale Drehbewegung.

- ### Optional: Verstellbare Objektiveinheiten
  Fokus- und Zoommotoren, die ebenfalls angesteuert werden können.

---

## 3. Software-Struktur

Die Software ist in mehrere Module unterteilt:

- ### src/main.py
  Startpunkt und Einstieg in die Anwendung. Initialisiert Systeme und Dienste, startet ggf. den Webserver.

- ### src/settings.py
  Enthält zentrale Einstellungen wie z.B.:
  - Serieller Port (DEVICE_NAME)
  - Baudrate (BAUD_RATE)
  - Motor-IDs (DXL_IDS)
  - Motor-Namen und Zuordnung der IDs (MOTOR_IDS, MOTOR_NAMES)
  - Aktuelle Stromlimits etc.

- ### src/dxl_manager.py
  Implementiert alle Funktionen, um die Dynamixel-Motoren zu steuern: 
  - Torque ein-/ausschalten
  - Positionsschreiben und -lesen
  - Geschwindigkeits- und Beschleunigungsprofile setzen
  - Feedback (Strom, Spannung, Temperatur etc.) auslesen

- ### src/modules/
  - profile_manager.py: Verwaltung von Bewegungsprofilen (z.B. Sets von Positionen, Geschwindigkeiten, Rampen für Filmsequenzen).
  - (weitere Module für Hardware- und spezifische Funktionen)

- ### src/web/
  - app.py: Flask-Anwendung (oder gegebenenfalls ein anderes Framework), um eine Weboberfläche zur Verfügung zu stellen.
  - templates/: HTML-Templates für die Weboberfläche (z.B. für das Auswählen von Profilen, Konfigurationen etc.).

Die Kommunikation mit den Motoren erfolgt per Dynamixel-SDK (Python-Bindings), was eine zuverlässige Ansteuerung ermöglicht.

---

## 4. Funktionsumfang

- ### Motorsteuerung
  - Bewegung auf definierte Positionen (Einzelbefehle und Bulk-Befehle)
  - Setzen von Geschwindigkeits- und Beschleunigungsparametern pro Motor
  - Ein-/Ausschalten von Torque, um den Motor zu entkoppeln

- ### Rückmeldungen (Feedback)
  - Positionsabfragen (Ist-Position) aller Motoren
  - Auslesen von Temperatur, Spannung und Strom
  - Erkennung von Fehlerzuständen

- ### Bewegungsprofile
  - Definierbare Sequenzen (z.B. Keyframes oder Wegpunkte)
  - Speicherung und Verwaltung über profile_manager.py
  - Geplante Funktionen: Interpolation zwischen Keyframes, zeitgesteuerte Abläufe

- ### Webinterface
  - Steuerung der wichtigsten Motorsetups (Slider, Turntable, Fokus etc.)
  - Einstellung der Beschleunigung und Geschwindigkeit
  - Starten/Stoppen von Bewegungen
  - (Zukünftig: Visualisierung von Profilen und Live-Daten)

---

## 5. Installation

1. ### Repository klonen
   » git clone https://github.com/USERNAME/camera_slider_project.git

2. ### Abhängigkeiten installieren
   - Python >= 3.7
   - Dynamixel-SDK (Python)
   - Flask (oder anderes Webframework, falls nötig)
   - Weitere Abhängigkeiten gemäß requirements.txt (falls vorhanden)

3. ### Konfiguration
   - Passen Sie die Einstellungen in src/settings.py an Ihr System an. 
     - DEVICE_NAME (z.B. /dev/ttyUSB0)
     - BAUD_RATE
     - Angeschlossene Motor-IDs

---

## 6. Konfiguration

Alle relevanten Parameter (z.B. Motor-IDs, Motor-Typen, Serienanschluss) befinden sich in src/settings.py. Diese Datei kann entsprechend der vorhandenen Hardware angepasst werden. Weitere Parameter, z.B. Eskalationsstufen bei Überhitzung etc., lassen sich dort ebenfalls pflegen.

---

## 7. Bedienungsanleitung

1. ### Software starten
   Führen Sie im Projektordner aus:
   » python3 src/main.py
   
   (Evtl. wird ein Flask-Server gestartet, erreichbar unter einer lokalen IP-Adresse.)

2. ### Motoren einschalten
   - Im Webinterface oder per Script (z.B. dxl_manager.enable_torque()) aktivieren.

3. ### Positionen setzen / Bewegungen ausführen
   - Entweder direkt per Python-Shell: 
     manager.bulk_write_goal_positions({1: 2048, 2: 1024})
   - Oder über das Webinterface (falls implementiert).

4. ### Profile speichern und abspielen
   - Ein Profil kann Beschleunigungs- und Geschwindigkeitskurven, sowie mehrere Zielpositionen enthalten.
   - Über den profile_manager werden diese gespeichert und verwaltet (Work in Progress).

5. ### Motoren ausschalten
   - Wichtig, wenn Sie manuell die Motorstellung verändern wollen oder das System nicht in Betrieb ist:
     manager.disable_torque()

---

## 8. Zukünftige Schritte

- Erweiterte Weboberfläche mit Visualisierung der aktuellen Position und des Bewegungsfortschritts
- Komplettes Keyframe-/Timelapse-System mit Interpolation und Speicherung mehrerer Sequenzen
- Automatische Fehlererkennung (z.B. bei Überlastung)
- Erweiterung des Systems um Pan/Tilt-Einheiten oder weitere Achsen
- Dokumentation der Hardware-Installation (Mechanik, Verkabelung etc.)

---

### Kontakt & Lizenz

Dieses Projekt ist aktuell als Open-Source-Projekt geplant. Für Fragen, Ideen und Feature-Wünsche nutzen Sie bitte die Issues-Funktion oder kontaktieren Sie uns per E-Mail (Adresse siehe Git-Profil).

Danke fürs Ausprobieren und Mitentwickeln!
