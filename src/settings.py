"""
Global settings and configuration for the camera slider project.
All constants and configuration parameters should be defined here.
"""

import logging
import os
from typing import Dict, List, Union

########################################
# Logging-Konfiguration
########################################
logging.basicConfig(level=logging.DEBUG)

########################################
# Kommunikations- und Hardware-Einstellungen
########################################
DEVICE_NAME = "/dev/ttyUSB0"  # Serial device for Dynamixel communication
BAUD_RATE = 2000000            # Communication speed with Dynamixel motors
PROTOCOL_VERSION = 2.0       # Dynamixel protocol version

########################################
# Dynamixel Register Addresses
########################################
MODEL_NUMBER_ADDR = 0        # Address for reading Model Number (most X-Series servos)
MODEL_NUMBER_LEN = 2         # Length of Model Number data
OPERATING_MODE = 3           # 3 = Position Control Mode (X-Series)
                            # 1 = Velocity Mode
                            # See Robotis eManual for other modes

########################################
# Motor-Konfiguration
########################################
MOTOR_IDS: Dict[str, int] = {
    # Name → ID mapping
    "turntable": 1,
    "slider": 2,
    "pan": 3,
    "tilt": 4,
    "zoom": 5,
    "focus": 6
}

MOTOR_NAMES: Dict[int, str] = {
    # ID → Name mapping (reverse of MOTOR_IDS)
    1: "turntable",
    2: "slider",
    3: "pan",
    4: "tilt",
    5: "zoom",
    6: "focus"
}

DXL_IDS: List[int] = [1, 2, 3, 4, 5, 6]  # List of all motor IDs in use

########################################
# Positions- und Geschwindigkeitseinstellungen
########################################
MOTOR_LIMITS: Dict[str, Dict[str, int]] = {
    "turntable": {"min": 0, "max": 4096},
    "slider": {"min": 0, "max": 89600},
    "pan": {"min": 760, "max": 3900},
    "tilt": {"min": 1360, "max": 2800},
    "zoom": {"min": 0, "max": 4096},
    "focus": {"min": 0, "max": 4096}
}

VELOCITY_LIMITS: Dict[str, int] = {
    "turntable": 1800,
    "slider": 2000,
    "pan": 1800,
    "tilt": 1800,
    "zoom": 1800,
    "focus": 1800
}

########################################
# Bewegungsparameter
########################################
DEFAULT_VELOCITY = 10000          # Default velocity in units/s
DEFAULT_ACCELERATION = 1800       # Default acceleration in units/s²
DEFAULT_DURATION = 10           # Default movement duration in seconds

# Position verification settings
POSITION_CHECK_INTERVAL = 0.05   # Interval for checking position updates (seconds)
POSITION_CHECK_TIMEOUT = 30      # Timeout for position checking (seconds)
POSITION_TOLERANCE = 4          # Position tolerance in steps
MAX_POSITION_RETRIES = 100      # Maximum retries for position verification

# Pan/Tilt spezifische Einstellungen
PAN_TILT_VELOCITY = 10          # Reduziert für sanftere Bewegungen
PAN_TILT_ACCELERATION = 1000      # Deutlich reduziert für weichere Beschleunigung
UPDATE_INTERVAL = 0.02          # Auf 50Hz gesetzt für stabileres Verhalten
PAN_TILT_TOLERANCE = 4          # Engere Toleranz für präzisere Bewegungen

########################################
# Konvertierungsfaktoren
########################################
CONVERSION_FACTORS: Dict[str, float] = {
    "turntable": 360 / 4096,    # 1 Umdrehung = 360 Grad
    "slider": 64 / 4096,        # 1 Umdrehung = 64 mm
    "pan": 360 / 4096,          # 1 Umdrehung = 360 Grad
    "tilt": 360 / 4096,         # 1 Umdrehung = 360 Grad
    "zoom": 360 / 4096,         # 1 Umdrehung = 360 Grad
    "focus": 360 / 4096         # 1 Umdrehung = 360 Grad
}

########################################
# Homing-Einstellungen
########################################
CURRENT_THRESHOLD = 80          # Schwellenwert für Strom in mA
MAX_HOMING_VELOCITY = 50        # Maximale Geschwindigkeit während des Homings

########################################
# Sicherheitsabschaltung: maximale Stromgrenzen
########################################
MAX_CURRENT_LIMITS: Dict[str, int] = {
    "turntable": 400,
    "slider": 400,
    "pan": 400,
    "tilt": 400,
    "zoom": 400,
    "focus": 400
}

########################################
# Fokus-Einstellungen
########################################
FOCUS_ENABLED = True           # Global focus control enable/disable
MIN_FOCUS_DISTANCE = 100      # Minimum focus distance in mm
MAX_FOCUS_DISTANCE = 2000     # Maximum focus distance in mm

########################################
# Slider-Einstellungen
########################################
SLIDER_STEP_TO_MM = 0.08789122581892  # 1 step = 0.08789122581892 mm
SLIDER_MAX_MM = 1300  # Maximum slider range in mm

########################################
# Kamera-Position und Offset-Einstellungen
########################################
TURNTABLE_POSITION: Dict[str, Union[int, float]] = {
    "x": -260,                # Horizontaler Versatz in mm
    "y": 600,               # Abstand entlang der Slider-Achse in mm
    "z": -295,              # Vertikaler Versatz in mm
    "DREHTELLER_OFFSET": 0  # Drehteller-Offset
}

MOTOR_OFFSETS: Dict[str, int] = {
    "pan": 180,              # Offset für Pan in Grad
    "tilt": 180,            # Korrigierter Offset für Tilt (20° mehr)
    "camera_to_tilt_pivot": 0
}

CAMERA_OFFSET_Z = 0         # Vertikaler Kamera-Offset

########################################
# Movement Sequence Settings
########################################
MOVEMENT_SETTINGS = {
    "primary_motors": {
        "position_tolerance": 4,     # Steps tolerance for position verification
        "max_retries": 200,          # Maximum position check retries
        "check_interval": 0.01,      # Reduced to 100Hz
    },
    "pan_tilt": {
        "position_tolerance": 4,     # Larger tolerance for pan/tilt
        "update_rate": 0.01,         # Changed to 100Hz
        "independent_movement": True  # Allow pan/tilt to move independently
    }
}

# Export settings for use in other modules
########################################
# Camera Settings
########################################
CAMERA_SETTINGS = {
    "capture": {
        "pre_delay": 0.2,        # Delay before capture (seconds)
        "post_delay": 0.2,       # Delay after capture (seconds)
    },
    "live_view": {
        "enabled": False,        # Live view default state
        "temp_dir": "/tmp/camera_preview",  # Directory for temporary preview files
        "update_rate": 0.01,      # Changed to 100Hz
    },
    "preview": {
        "width": 854,           # Preview image width
        "height": 480,          # Preview image height
        "quality": 85,          # JPEG quality for preview
    }
}

# Create temporary directory for camera preview files
os.makedirs(CAMERA_SETTINGS["live_view"]["temp_dir"], exist_ok=True)

########################################
# Motion Control Configuration
########################################
MOTION_CONTROL = {
    # Master-Slave Konfiguration
    "master_motor": "slider",
    "synchronized_motors": {
        "pan": {
            "master": "slider",
            "prediction_enabled": True
        },
        "tilt": {
            "master": "slider",
            "prediction_enabled": True
        }
    },
    
    # Kalman Filter Einstellungen für Slave-Motoren
    "slave_kalman": {
        "update_rate": 0.02,        # 50Hz Update-Rate für stabileres Verhalten
        "process_noise": {          # Process Noise (Q) Parameter
            "position": 0.001,      # Stark reduziert für stabilere Position
            "velocity": 0.01,       # Reduziert für sanftere Geschwindigkeitsänderungen
            "acceleration": 0.05    # Reduziert für weichere Beschleunigung
        },
        "measurement_noise": 0.5,   # Erhöht für stärkere Glättung
        "initial_uncertainty": 50   # Reduziert für konservativeres Startverhalten
    },
    
    # Bewegungsprädiktion für Slave-Motoren
    "prediction": {
        "min_time": 0.01,          # Längere Mindestvorhersage (10ms)
        "max_time": 0.1,           # Längere Maximalvorhersage (100ms)
        "time": 0.02,              # Standard auf 20ms für sanftere Übergänge
        "smoothing": {
            "min_factor": 0.05,     # Stärkere Mindestglättung
            "max_factor": 0.9,     # Reduzierte Maximalglättung für mehr Stabilität
            "velocity_scale": 0.001 # Angepasst für bessere Geschwindigkeitsglättung
        }
    },
    
    # Fehlerbehandlung
    "error_handling": {
        "max_prediction_error": 10,  # Reduziert für frühere Fehlerkorrektur
        "recovery_factor": 0.4,     # Stark reduziert für sehr sanfte Fehlerkorrektur
        "monitoring": {
            "temperature": {
                "warning": 55,      # °C
                "error": 65         # °C
            },
            "voltage": {
                "warning": 11.5,    # V
                "error": 11.0       # V
            },
            "current": {
                "warning": 800,     # mA
                "error": 1000       # mA
            },
            "load": {
                "warning": 0,      # %
                "error": 0        # %
            }
        }
    }
}

# Reverse lookup für Motor-IDs zu Namen
MOTOR_ID_TO_NAME = {v: k for k, v in MOTOR_IDS.items()}

# Auto-detected camera settings options
CAMERA_AUTO_SETTINGS = {
    "iso": ["Auto", "100", "200", "400", "800", "1600", "3200", "6400"],
    "aperture": ["Auto", "1.8", "2.0", "2.8", "4.0", "5.6", "8.0", "11", "16"],
    "shutterspeed": ["Auto", "1/4000", "1/2000", "1/1000", "1/500", "1/250", "1/125", "1/60", "1/30", "1/15"],
    "whitebalance": ["Auto", "Daylight", "Shade", "Cloudy", "Tungsten", "Fluorescent", "Flash", "Custom"],
}

__all__ = [
    "DEVICE_NAME", "BAUD_RATE", "PROTOCOL_VERSION",
    "MODEL_NUMBER_ADDR", "MODEL_NUMBER_LEN", "OPERATING_MODE",
    "MOTOR_IDS", "MOTOR_NAMES", "DXL_IDS",
    "MOTOR_LIMITS", "VELOCITY_LIMITS", "CONVERSION_FACTORS",
    "DEFAULT_VELOCITY", "DEFAULT_ACCELERATION", "DEFAULT_DURATION",
    "POSITION_CHECK_INTERVAL", "POSITION_CHECK_TIMEOUT",
    "POSITION_TOLERANCE", "MAX_POSITION_RETRIES",
    "PAN_TILT_VELOCITY", "PAN_TILT_ACCELERATION", "UPDATE_INTERVAL",
    "PAN_TILT_TOLERANCE", "CURRENT_THRESHOLD", "MAX_HOMING_VELOCITY",
    "MAX_CURRENT_LIMITS", "FOCUS_ENABLED",
    "MIN_FOCUS_DISTANCE", "MAX_FOCUS_DISTANCE",
    "SLIDER_STEP_TO_MM", "SLIDER_MAX_MM",
    "TURNTABLE_POSITION", "MOTOR_OFFSETS", "CAMERA_OFFSET_Z",
    "MOVEMENT_SETTINGS", "CAMERA_SETTINGS", "CAMERA_AUTO_SETTINGS",
    "KALMAN_SETTINGS", "MOTION_CONTROL"  # Neue Settings hinzugefügt
]
