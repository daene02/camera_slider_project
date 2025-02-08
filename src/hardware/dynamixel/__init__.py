"""Dynamixel Hardware Module"""

from .constants import *
from .base_manager import DynamixelBaseManager
from .motion_manager import DynamixelMotionManager
from .pid_manager import DynamixelPIDManager
from .status_manager import DynamixelStatusManager

class DynamixelManager(DynamixelMotionManager, DynamixelPIDManager, DynamixelStatusManager):
    """
    Hauptklasse für die Dynamixel-Servomotor-Steuerung.
    Erbt von allen spezialisierten Manager-Klassen.
    """
    pass

__all__ = [
    'DynamixelManager',
    'DynamixelBaseManager',
    'DynamixelMotionManager',
    'DynamixelPIDManager',
    'DynamixelStatusManager'
]
