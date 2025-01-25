# settings.py

# Logging-Konfiguration
import logging
logging.basicConfig(level=logging.DEBUG)

# Motor Konfiguration
BAUDRATE = 57600
DEVICENAME = "/dev/ttyUSB0"
PROTOCOL_VERSION = 2.0
MOTOR_IDS = {"turntable": 1, "slider": 2, "pan": 3, "tilt": 4, "camera_zoom": 5, "turntable_tilt": 6}
MOTOR_NAMES = {
    1: "turntable",
    2: "slider",
    3: "pan",
    4: "tilt",
    5: "camera_zoom",
    6: "turntable_tilt"
}   
MOTOR_LIMITS = {
    "turntable": {"min": 0, "max": 4096},
    "slider": {"min": 0, "max": 89600},
    "pan": {"min": 760, "max": 3900},
    "tilt": {"min": 1360, "max": 2800},
}
CONVERSION_FACTORS = {
    "turntable": 360 / 4096,      # 1 Umdrehung = 360 Grad
    "slider": 64 / 4096,         # 1 Umdrehung = 64 mm (1 Schritt in mm)
    "pan": 360 / 4096,           # 1 Umdrehung = 360 Grad
    "tilt": 360 / 4096,          # 1 Umdrehung = 360 Grad
    "camera_zoom": 360 / 4096,   # 1 Umdrehung = 360 Grad
    "turntable_tilt": 360 / 4096 # 1 Umdrehung = 360 Grad
}
VELOCITY_LIMITS = {
    "turntable": 1800,
    "slider": 2000,
    "pan": 1800,
    "tilt": 1800
}

# Dynamixel-Register-Adressen
TORQUE_ENABLE = 64
GOAL_POSITION = 116
GOAL_VELOCITY = 104  # Zielgeschwindigkeit
PROFILE_VELOCITY = 112
PROFILE_ACCELERATION = 108
OPERATING_MODE = 11
DRIVE_MODE = 10
PRESENT_POSITION = 132
PRESENT_VELOCITY = 128
PRESENT_LOAD = 126
PRESENT_TEMPERATURE = 146
PRESENT_VOLTAGE = 144
PRESENT_CURRENT = 126
PRESENT_TORQUE = 126
MODEL_NUMBER = 0  # Register-Adresse für Model Number
MOVING = 122
HOMING_OFFSET = 20  # Register-Adresse für Homing Offset
CURRENT_LIMIT = 38  # Register für maximale Stromgrenze
GOAL_CURRENT = 102  # Register für Zielstrom
VELOCITY_LIMIT = 44  # Register für maximale Geschwindigkeit
MIN_POSITION_LIMIT = 52  # Minimaler Positionsgrenzwert
MAX_POSITION_LIMIT = 48  # Maximaler Positionsgrenzwert
VELOCITY_LIMIT_ADDRESS = 44  # Register-Adresse für Velocity Limit
VELOCITY_I_GAIN = 76  # Register für Velocity I Gain
VELOCITY_P_GAIN = 78  # Register für Velocity P Gain
POSITION_D_GAIN = 80  # Register für Position D Gain
POSITION_I_GAIN = 82  # Register für Position I Gain
POSITION_P_GAIN = 84  # Register für Position P Gain
LEN_PRO_GOAL_POSITION = 4  # Length of goal position data
LEN_PRO_PRESENT_POSITION = 4  # Length of present position data
LEN_PRO_PRESENT_VELOCITY = 4  # Length of present velocity data
LEN_PRO_PRESENT_LOAD = 2  # Length of present load data
LEN_PRO_PRESENT_TEMPERATURE = 1  # Length of present temperature data
LEN_PRO_PRESENT_VOLTAGE = 2
LEN_PRO_PRESENT_CURRENT = 2
LEN_PRO_PRESENT_TORQUE = 2
DXL_IDS = [1, 2, 3, 4, 5, 6]  # Example motor IDs

# Standardwerte für PID-Regler pro Motor
PID_DEFAULTS = {
    "turntable": {
        "velocity_i_gain": 1920,
        "velocity_p_gain": 100,
        "position_d_gain": 0,
        "position_i_gain": 0,
        "position_p_gain": 800,        
    },
    "slider": {
        "velocity_i_gain": 1920,
        "velocity_p_gain": 100,
        "position_d_gain": 0,
        "position_i_gain": 0,
        "position_p_gain": 800,        
    },
    "pan": {
        "velocity_i_gain": 1920,
        "velocity_p_gain": 50,
        "position_d_gain": 100,
        "position_i_gain": 0,
        "position_p_gain": 800,       
    },
    "tilt": {
        "velocity_i_gain": 1920,
        "velocity_p_gain": 50,
        "position_d_gain": 100,
        "position_i_gain": 0,
        "position_p_gain": 800,
    },
    "camera_zoom": {
        "velocity_i_gain": 1920,
        "velocity_p_gain": 100,
        "position_d_gain": 0,
        "position_i_gain": 0,
        "position_p_gain": 800,
    },
    "turntable_tilt": {
        "velocity_i_gain": 1920,
        "velocity_p_gain": 100,
        "position_d_gain": 0,
        "position_i_gain": 0,
        "position_p_gain": 800,
    }
}

# Bulk Read-Einstellungen
BULK_READ_PARAMS = [
    {"address": PRESENT_POSITION, "length": LEN_PRO_PRESENT_POSITION},
    {"address": PRESENT_CURRENT, "length": LEN_PRO_PRESENT_CURRENT},
    {"address": PRESENT_TEMPERATURE, "length": LEN_PRO_PRESENT_TEMPERATURE},
    {"address": PRESENT_VOLTAGE, "length": LEN_PRO_PRESENT_VOLTAGE},
    {"address": PRESENT_TORQUE, "length": LEN_PRO_PRESENT_TORQUE},
]

# Homing-Einstellungen
CURRENT_THRESHOLD = 80  # Schwellenwert für Strom in mA
MAX_HOMING_VELOCITY = 50  # Maximale Geschwindigkeit während des Homings

# Maximale Stromgrenzen für Sicherheitsabschaltung
MAX_CURRENT_LIMITS = {
    "turntable": 300,  # Maximaler Strom in mA
    "slider": 300,
    "pan": 300,
    "tilt": 300,
    "camera_zoom": 300,
    "turntable_tilt": 300
}
MOTOR_NAMES = {
    1: "turntable",
    2: "slider",
    3: "pan",
    4: "tilt",
    5: "camera_zoom",
    6: "turntable_tilt"
}

# Drehteller Fokus-Parameter
TURNTABLE_POSITION = {
    "x": 260,   # Horizontaler Versatz in mm
    "y": 600,  # Abstand entlang der Slider-Achse in mm
    "z": -295,  # Vertikaler Versatz in mm
    "DREHTELLER_OFFSET": 00  # Beispielwert: 100 mm außerhalb der Mitte
}

# Offset-Werte für Motorpositionen
MOTOR_OFFSETS = {
    "pan": -180,   # Offset für Pan in Grad
    "tilt": -180,   # Offset für Tilt in Grad
    "camera_to_tilt_pivot": 0  # Vertikaler Abstand von der Kamera zum Drehpunkt des Tilt-Motors
}
