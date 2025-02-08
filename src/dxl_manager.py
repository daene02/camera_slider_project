"""
Haupt-Interface für Dynamixel Servomotoren.
Diese Datei ist jetzt ein Wrapper für das neue modulare Dynamixel-System.
"""

from src.hardware.dynamixel import DynamixelManager

# Re-export der Hauptklasse für Abwärtskompatibilität
__all__ = ['DynamixelManager']
