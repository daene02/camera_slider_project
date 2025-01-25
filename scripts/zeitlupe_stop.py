from motor_control.motor_control import MotorController
from settings import MOTOR_IDS, TURNTABLE_POSITION, PID_DEFAULTS, MOTOR_LIMITS, PROFILE_VELOCITY, PROFILE_ACCELERATION, LEN_PRO_GOAL_POSITION, LEN_PRO_PRESENT_POSITION, MOTOR_NAMES
from motor_control.bulk import BulkOperations
import math
import numpy as np
from scipy.interpolate import CubicSpline
import time
import os
import json
import settings

PROFILES_FILE = "/home/pi/camera_slider_project/profiles/profiles.json"

VELOCITY_LIMITS = {
    "turntable": 1800,
    "slider": 2000,
    "pan": 1800,
    "tilt": 1800
}

CONVERSION_FACTORS = {
    "slider": 0.015,  # Schritte -> mm
    "pan": 0.0878906,  # Schritte -> Grad
    "tilt": 0.0878906,  # Schritte -> Grad
    "turntable": 0.0878906  # Schritte -> Grad
}

class MotorControllerWithFocus(MotorController):
    def __init__(self):
        super().__init__()
        self.bulk_operations = BulkOperations(self.port_handler, self.packet_handler)

    def bulk_read_positions(self):
        motor_ids = list(MOTOR_IDS.values())
        positions = self.bulk_operations.bulk_read_all(motor_ids)
        if positions is None:
            raise RuntimeError("Bulk-Read fehlgeschlagen: Keine Positionsdaten verfügbar. Überprüfen Sie die Verbindung zu den Motoren.")

        converted_positions = {}
        for motor_name, motor_id in MOTOR_IDS.items():
            raw_position = positions.get(motor_id, {}).get("position", 0)
            conversion_factor = CONVERSION_FACTORS.get(motor_name, 1)
            converted_positions[motor_name] = round(raw_position * conversion_factor, 2)

        print("[DEBUG] Bulk read positions (in mm/deg):", converted_positions)
        return converted_positions

    def bulk_write_positions(self, target_positions):
        converted_positions = {}
        for motor_name, target_position in target_positions.items():
            conversion_factor = CONVERSION_FACTORS.get(motor_name, 1)
            converted_positions[motor_name] = int(target_position / conversion_factor)

        print("[DEBUG] Bulk write positions (converted to steps):", converted_positions)
        try:
            self.bulk_operations.bulk_write_all(converted_positions)
            print("[INFO] Positionen erfolgreich geschrieben.")
        except Exception as e:
            print(f"[ERROR] Fehler beim Schreiben der Positionen: {e}")
            raise e

    def set_profile(self, motor_id, velocity, acceleration):
        """
        Setzt die Geschwindigkeit und Beschleunigung für einen Motor über Bulk-Schreiboperationen.
        """
        try:
            velocity = min(velocity, VELOCITY_LIMITS[MOTOR_NAMES[motor_id]])  # Begrenzung der Geschwindigkeit
            target_values = {
                motor_id: {
                    "velocity": velocity,
                    "acceleration": acceleration
                }
            }

            print(f"[DEBUG] Set profile for Motor {motor_id}: Geschwindigkeit={velocity}, Beschleunigung={acceleration}")

            self.bulk_operations.bulk_write_all(target_values)
            print(f"[INFO] Profil für Motor {motor_id} erfolgreich gesetzt.")
        except Exception as e:
            print(f"[ERROR] Fehler beim Setzen des Profils für Motor {motor_id}: {e}")
            raise e

    def smooth_trajectory(self, positions, resolution=3000):
        x = np.linspace(0, len(positions["slider"]) - 1, len(positions["slider"]))
        smoothed = {}

        for axis, values in positions.items():
            spline = CubicSpline(x, values)
            smoothed[axis] = spline(np.linspace(0, len(positions["slider"]) - 1, resolution))

        return smoothed

    def synchronize_movements(self, positions, resolution=3000, duration=10):
        smoothed_positions = self.smooth_trajectory(positions, resolution)
        step_duration = duration / resolution

        print("Aktiviere Drehmoment für alle Motoren...")
        for motor_id in MOTOR_IDS.values():
            self.enable_torque(motor_id)

        for i in range(resolution):
            current_positions = self.bulk_read_positions()
            target_positions = {}

            for motor_name in positions:
                position = smoothed_positions[motor_name][i]

                if not self.validate_target(motor_name, position):
                    continue

                velocity = abs(position - current_positions[motor_name]) / step_duration
                velocity = min(velocity, VELOCITY_LIMITS[motor_name])  # Geschwindigkeit begrenzen
                print(f"Motor: {motor_name}, Ziel: {position} mm/deg, Geschwindigkeit: {velocity} mm/deg pro Sekunde")
                self.set_profile(MOTOR_IDS[motor_name], int(velocity), acceleration=500)
                target_positions[motor_name] = position

            self.bulk_write_positions(target_positions)
            time.sleep(step_duration)

controller = MotorControllerWithFocus()

slider_positions = [0, 100, 300, 450, 600, 750, 900, 750, 600, 600, 600, 300, 100, 0]
turntable_positions = [0, 45, 90, 180, 180, 270, 180, 180, 90, 180, 360, 90, 45, 0]

focus_enabled = True
camera_offset_z = 0

controller.initialize_focus(slider_positions, turntable_positions, duration=5, resolution=1000, focus_enabled=focus_enabled, camera_offset_z=camera_offset_z)

print("Kamera-Fokussteuerung abgeschlossen.")
