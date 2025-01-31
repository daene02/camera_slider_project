import logging

########################################
# Logging-Konfiguration
########################################
logging.basicConfig(level=logging.DEBUG)

########################################
# Kommunikations- und Hardware-Einstellungen
########################################
DEVICE_NAME = "/dev/ttyUSB0"  # Ehemals DEVICENAME
BAUD_RATE = 57600           # Ehemals BAUDRATE
PROTOCOL_VERSION = 2.0

########################################
# Motor-Konfiguration
########################################
MOTOR_IDS = {
    # Name → ID
    "turntable": 1,
    "slider": 2,
    "pan": 3,
    "tilt": 4,
    "zoom": 5,
    "focus": 6
}

MOTOR_NAMES = {
    # ID → Name
    1: "turntable",
    2: "slider",
    3: "pan",
    4: "tilt",
    5: "zoom",
    6: "focus"
}

DXL_IDS = [1, 2, 3, 4, 5, 6]  # Gesamte Liste aller verwendeten Motor-IDs

########################################
# Positions- und Geschwindigkeitseinstellungen
########################################
MOTOR_LIMITS = {
    "turntable": {"min": 0, "max": 4096},
    "slider": {"min": 0, "max": 89600},
    "pan": {"min": 760, "max": 3900},
    "tilt": {"min": 1360, "max": 2800},
    "zoom": {"min": 0, "max": 4096},
    "focus": {"min": 0, "max": 4096}
}

VELOCITY_LIMITS = {
    "turntable": 1800,
    "slider": 2000,
    "pan": 1800,
    "tilt": 1800,
    "zoom": 1800,
    "focus": 1800
}

CONVERSION_FACTORS = {
    "turntable": 360 / 4096,      # 1 Umdrehung = 360 Grad
    "slider": 64 / 4096,         # 1 Umdrehung = 64 mm
    "pan": 360 / 4096,           # 1 Umdrehung = 360 Grad
    "tilt": 360 / 4096,          # 1 Umdrehung = 360 Grad
    "zoom": 360 / 4096,   # 1 Umdrehung = 360 Grad
    "focus": 360 / 4096 # 1 Umdrehung = 360 Grad
}



########################################
# Homing-Einstellungen
########################################
CURRENT_THRESHOLD = 80      # Schwellenwert für Strom in mA
MAX_HOMING_VELOCITY = 50    # Maximale Geschwindigkeit während des Homings

########################################
# Sicherheitsabschaltung: maximale Stromgrenzen
########################################
MAX_CURRENT_LIMITS = {
    "turntable": 300,
    "slider": 300,
    "pan": 300,
    "tilt": 300,
    "zoom": 300,
    "focus": 300
}

########################################
# Drehteller Fokus-Parameter
########################################
TURNTABLE_POSITION = {
    "x": 260,    # Horizontaler Versatz in mm
    "y": 600,    # Abstand entlang der Slider-Achse in mm
    "z": -295,   # Vertikaler Versatz in mm
    "DREHTELLER_OFFSET": 0  # Beispielwert
}

########################################
# Offset-Werte
########################################
MOTOR_OFFSETS = {
    "pan": 180,   # Offset für Pan in Grad
    "tilt": 180,  # Offset für Tilt in Grad
    "camera_to_tilt_pivot": 0
}

# Export settings for use in other modules
__all__ = [
    "DEVICE_NAME", "BAUD_RATE", "PROTOCOL_VERSION", "MOTOR_IDS", "MOTOR_NAMES",
    "DXL_IDS", "MOTOR_LIMITS", "VELOCITY_LIMITS", "CONVERSION_FACTORS",
    "CURRENT_THRESHOLD", "MAX_HOMING_VELOCITY", "MAX_CURRENT_LIMITS",
    "TURNTABLE_POSITION", "MOTOR_OFFSETS"
]
