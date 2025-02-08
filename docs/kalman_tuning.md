# Kalman Filter & Bewegungsprädiktion Einstellungshilfe

## Inhaltsverzeichnis
1. [Schnelle Bewegungen](#schnelle-bewegungen)
2. [Präzise Bewegungen](#präzise-bewegungen)
3. [Normale Bewegungen](#normale-bewegungen)
4. [Parameterdetails](#parameterdetails)
5. [Fehlerbehebung](#fehlerbehebung)

## Vorbereitungen
- Öffnen Sie `src/settings.py`
- Suchen Sie den `MOTION_CONTROL` Bereich
- Sichern Sie Ihre aktuellen Einstellungen

## Schnelle Bewegungen

Optimiert für schnelle Reaktion und hohe Geschwindigkeit.

```python
"slave_kalman": {
    "update_rate": 0.01,        # 100Hz für schnelle Updates
    "process_noise": {
        "position": 0.01,       # Höher für schnellere Positionsanpassung
        "velocity": 0.08,       # Höher für schnellere Geschwindigkeitsänderungen
        "acceleration": 0.15    # Höher für schnellere Beschleunigungsanpassung
    },
    "measurement_noise": 0.4,   # Ausgewogen für schnelle Reaktion
    "initial_uncertainty": 100  # Höher für schnellere initiale Anpassung
},
"prediction": {
    "min_time": 0.001,         # Sehr kurze Mindestzeit
    "max_time": 0.03,          # Kürzere Maximalzeit
    "smoothing": {
        "min_factor": 0.2,     # Weniger Glättung
        "max_factor": 0.9,     # Schnellere Anpassung
        "velocity_scale": 0.001 # Größer für schnellere Geschwindigkeit
    }
}
```

### Effekte
- Sehr schnelle Reaktion auf Bewegungen
- Geringere Verzögerung bei Richtungsänderungen
- Kann bei sehr schnellen Bewegungen leicht zittern
- Gut für dynamische Aufnahmen

## Präzise Bewegungen

Optimiert für maximale Stabilität und Genauigkeit.

```python
"slave_kalman": {
    "update_rate": 0.01,        # 100Hz Standard
    "process_noise": {
        "position": 0.003,      # Sehr niedrig für hohe Präzision
        "velocity": 0.03,       # Niedriger für stabilere Geschwindigkeit
        "acceleration": 0.08    # Niedriger für sanftere Beschleunigung
    },
    "measurement_noise": 0.6,   # Höher für mehr Glättung
    "initial_uncertainty": 50   # Niedriger für vorsichtigere Schätzung
},
"prediction": {
    "min_time": 0.003,         # Längere Mindestzeit
    "max_time": 0.05,          # Längere Maximalzeit
    "smoothing": {
        "min_factor": 0.1,     # Mehr Glättung
        "max_factor": 0.7,     # Sanftere Übergänge
        "velocity_scale": 0.0003 # Kleiner für sanftere Geschwindigkeit
    }
}
```

### Effekte
- Sehr stabile Bewegungen
- Minimales Zittern
- Längere Reaktionszeit
- Ideal für Makroaufnahmen und Zeitraffer

## Normale Bewegungen

Ausgewogene Einstellungen für allgemeine Verwendung.

```python
"slave_kalman": {
    "update_rate": 0.01,        # 100Hz Standard
    "process_noise": {
        "position": 0.005,      # Ausgewogen
        "velocity": 0.05,       # Ausgewogen
        "acceleration": 0.1     # Ausgewogen
    },
    "measurement_noise": 0.5,   # Ausgewogen
    "initial_uncertainty": 80   # Ausgewogen
},
"prediction": {
    "min_time": 0.002,         # Ausgewogen
    "max_time": 0.04,          # Ausgewogen
    "smoothing": {
        "min_factor": 0.15,    # Ausgewogen
        "max_factor": 0.85,    # Ausgewogen
        "velocity_scale": 0.0005 # Ausgewogen
    }
}
```

### Effekte
- Guter Kompromiss zwischen Geschwindigkeit und Präzision
- Stabile aber reaktive Bewegungen
- Geeignet für die meisten Aufnahmesituationen

## Parameterdetails

### Process Noise (Q)
- **position**: Bestimmt wie schnell der Filter Positionsänderungen folgt
  - Höher = schnellere Reaktion, mehr Zittern
  - Niedriger = stabilere Position, langsamere Reaktion
  
- **velocity**: Kontrolliert die Geschwindigkeitsanpassung
  - Höher = schnellere Geschwindigkeitsänderungen
  - Niedriger = gleichmäßigere Geschwindigkeit
  
- **acceleration**: Beeinflusst die Beschleunigungsänderungen
  - Höher = schnellere Beschleunigungsanpassung
  - Niedriger = sanftere Geschwindigkeitsübergänge

### Measurement Noise (R)
- Höher = mehr Glättung, langsamere Reaktion
- Niedriger = schnellere Reaktion, mehr Zittern möglich

### Initial Uncertainty (P0)
- Höher = schnellere anfängliche Anpassung
- Niedriger = vorsichtigere anfängliche Schätzungen

### Prediction Settings
- **min_time/max_time**: Zeitfenster für Vorhersagen
- **smoothing factors**: Beeinflussen die Bewegungsglättung
  - min_factor: Minimale Glättung
  - max_factor: Maximale Glättung
  - velocity_scale: Geschwindigkeitsabhängige Glättung

## Fehlerbehebung

### Symptom: Zittern bei schnellen Bewegungen
1. Process Noise velocity erhöhen
2. Smoothing max_factor reduzieren
3. Measurement noise leicht erhöhen

### Symptom: Zu langsame Reaktion
1. Process Noise position erhöhen
2. Measurement noise reduzieren
3. min_time und max_time reduzieren

### Symptom: Überschwingen
1. Process Noise acceleration reduzieren
2. Smoothing min_factor erhöhen
3. max_time erhöhen

### Symptom: Verzögerte Positionsanzeige
1. Update rate überprüfen (sollte 0.01 sein)
2. Process Noise position leicht erhöhen
3. Initial uncertainty erhöhen

## Anpassungsprozess

1. Starten Sie mit den "Normalen Bewegungen" Einstellungen
2. Testen Sie die Bewegung
3. Identifizieren Sie das Hauptproblem
4. Passen Sie NUR EINEN Parameter an
5. Testen Sie erneut
6. Wiederholen Sie, bis das gewünschte Verhalten erreicht ist

## Wichtige Hinweise

- Ändern Sie immer nur einen Parameter auf einmal
- Machen Sie kleine Änderungen (max. 20-30%)
- Testen Sie nach jeder Änderung
- Notieren Sie sich die besten Einstellungen
- Bei Problemen: Zurück zu den Standard-Einstellungen
