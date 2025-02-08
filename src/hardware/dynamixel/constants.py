"""Dynamixel Register und Konstanten"""

# Kommunikationseinstellungen
PROTOCOL_VERSION               = 2.0
BAUDRATE                      = 2000000
DEVICENAME                    = "/dev/ttyUSB0"

# Register-Adressen
ADDR_PRO_TORQUE_ENABLE         = 64
ADDR_PRO_GOAL_POSITION         = 116
ADDR_PRO_PRESENT_POSITION      = 132
ADDR_PRO_PROFILE_ACCEL         = 108
ADDR_PRO_PROFILE_VELOC         = 112
ADDR_PRO_PRESENT_TEMPERATURE   = 146
ADDR_PRO_PRESENT_VOLTAGE       = 144
ADDR_PRO_PRESENT_CURRENT       = 126

# Position PID Register
ADDR_PRO_POSITION_D_GAIN      = 80
ADDR_PRO_POSITION_I_GAIN      = 82
ADDR_PRO_POSITION_P_GAIN      = 84

# Velocity PID Register
ADDR_PRO_VELOCITY_I_GAIN      = 76  # Register für Velocity I Gain
ADDR_PRO_VELOCITY_P_GAIN      = 78  # Register für Velocity P Gain

# Registerlängen
LEN_PRO_GOAL_POSITION          = 4
LEN_PRO_PRESENT_POSITION       = 4
LEN_PRO_PROFILE_PARAM          = 4
LEN_PRO_PRESENT_TEMPERATURE    = 1
LEN_PRO_PRESENT_VOLTAGE        = 2
LEN_PRO_PRESENT_CURRENT        = 2
LEN_PRO_PID_GAIN              = 2

# Standard Motor-IDs
DXL_IDS                        = [1, 2, 3, 4, 5, 6]

# PID Wertebereiche
VELOCITY_PID_RANGES = {
    'p': {'min': 1000, 'max': 16383},
    'i': {'min': 1, 'max': 16383}
}
