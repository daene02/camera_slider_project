from src.dxl_manager import DynamixelManager
from src.settings import MOTOR_IDS, MOTOR_LIMITS, MOTOR_NAMES, VELOCITY_LIMITS, CONVERSION_FACTORS, MOTOR_OFFSETS
import math
import numpy as np
from scipy.interpolate import CubicSpline
import time
import os
import json
import src.settings

PROFILES_FILE = "/home/pi/camera_slider_project/profiles/profiles.json"

class MotorControllerWithFocus:
    def __init__(self):
        self.manager = DynamixelManager(
            device="/dev/ttyUSB0",
            baud=57600,
            protocol=2.0,
            dxl_ids=list(MOTOR_IDS.values())
        )

    def bulk_read_positions(self):
        dxl_positions = self.manager.bulk_read_positions()
        if dxl_positions is None:
            raise RuntimeError("Bulk-Read fehlgeschlagen: Keine Positionsdaten verfügbar. Überprüfen Sie die Verbindung zu den Motoren.")

        # Konvertiere Schritte in mm/grad und wende Offsets an
        converted_positions = {}
        for motor_name, motor_id in MOTOR_IDS.items():
            steps = dxl_positions.get(motor_id, 0)
            conversion = CONVERSION_FACTORS[motor_name]
            
            # Ensure the steps are within the valid range
            if motor_name == "pan":
                min_steps, max_steps = 0, 3900
            elif motor_name == "tilt":
                min_steps, max_steps = 0, 2800
            else:
                min_steps, max_steps = 0, float('inf')  # Default range for other motors
            
            if steps < min_steps or steps > max_steps:
                print(f"Zielwert {steps} für Motor {motor_name} liegt außerhalb der Grenzen ({min_steps}, {max_steps}).")
                steps = max(min(steps, max_steps), min_steps)
            
            # Konvertiere Schritte in mm oder Grad
            real_value = steps * conversion
            
            # Wende Offsets für Pan und Tilt an
            if motor_name in ["pan", "tilt"]:
                real_value -= MOTOR_OFFSETS.get(motor_name, 0)
                
            converted_positions[motor_name] = real_value
            
        print("[DEBUG] Konvertierte Positionen:", converted_positions)
        return converted_positions

    def bulk_write_positions(self, target_positions):
        print("[DEBUG] Ziel-Positionen (mm/grad):", target_positions)
        try:
            # Konvertiere mm/grad in Schritte und wende Offsets an
            dxl_targets = {}
            for motor_name, position in target_positions.items():
                # Entferne Offset für Pan und Tilt
                if motor_name in ["pan", "tilt"]:
                    position += MOTOR_OFFSETS.get(motor_name, 0)
                
                # Konvertiere mm/grad in Schritte
                conversion = CONVERSION_FACTORS[motor_name]
                steps = int(position / conversion)
                
                dxl_targets[MOTOR_IDS[motor_name]] = steps
            
            print("[DEBUG] Ziel-Positionen (Schritte):", dxl_targets)
            # ...existing code to write positions to motors...
        except Exception as e:
            print(f"[ERROR] Fehler beim Schreiben der Positionen: {e}")
            raise e

    def initialize_focus(self, slider_positions, turntable_positions, duration=10, resolution=1000, focus_enabled=False, camera_offset_z=0):
        """
        Initialisiert die Fokussteuerung und synchronisiert die Bewegungen.
        :param slider_positions: Liste der Slider-Positionen
        :param turntable_positions: Liste der Turntable-Positionen
        :param duration: Dauer der Bewegung
        :param resolution: Anzahl der Schritte für die Interpolation
        :param focus_enabled: Aktiviert die Fokusberechnung (True/False)
        :param camera_offset_z: Offset der Kamera in Z-Richtung
        """
        print("Initialisiere Fokussteuerung...")

        positions = {
            "slider": slider_positions,
            "turntable": turntable_positions
        }

        if focus_enabled:
            positions["pan"] = [0] * len(slider_positions)  # Beispiel für Pan
            positions["tilt"] = [0] * len(slider_positions)  # Beispiel für Tilt

        self.synchronize_movements(positions, resolution=resolution, duration=duration)
        print("Fokussteuerung abgeschlossen.")

    def set_profile(self, motor_id, velocity, acceleration):
        """
        Setzt die Geschwindigkeit und Beschleunigung für einen Motor über Bulk-Schreiboperationen.
        """
        try:
            motor_name = MOTOR_NAMES[motor_id]
            max_velocity = MOTOR_LIMITS[motor_name].get("max_velocity", VELOCITY_LIMITS[motor_name])
            velocity = min(velocity, max_velocity)  # Begrenzung der Geschwindigkeit
            
            dxl_targets = { motor_id: velocity }
            self.manager.bulk_write_profile_velocity(dxl_targets)
            dxl_targets = { motor_id: acceleration }
            self.manager.bulk_write_profile_acceleration(dxl_targets)

            print(f"[DEBUG] Set profile for Motor {motor_id}: Geschwindigkeit={velocity}, Beschleunigung={acceleration}")
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
        self.manager.enable_torque()

        for i in range(resolution):
            current_positions = self.bulk_read_positions()
            target_positions = {}

            for motor_name in positions:
                position = smoothed_positions[motor_name][i]

                if not self._validate_target(motor_name, position):
                    continue

                velocity = abs(position - current_positions[motor_name]) / step_duration
                velocity = min(velocity, MOTOR_LIMITS[motor_name].get("max_velocity", 32767))  # Geschwindigkeit begrenzen
                print(f"Motor: {motor_name}, Ziel: {position} mm/deg, Geschwindigkeit: {velocity} mm/deg pro Sekunde")
                
                # Ausgabe der Berechnungsergebnisse für pan und tilt
                if motor_name in ["pan", "tilt"]:
                    print(f"Berechnungsergebnis für {motor_name}: Zielwert = {position}, Geschwindigkeit = {velocity}")

                self.set_profile(MOTOR_IDS[motor_name], int(velocity), acceleration=500)
                target_positions[motor_name] = position

            self.bulk_write_positions(target_positions)
            time.sleep(step_duration)

    def _validate_target(self, motor_name, target_value):
        """
        Überprüft, ob der Zielwert im gültigen Bereich für den Motor liegt.
        :param motor_name: Name des Motors
        :param target_value: Zielwert
        :return: True, wenn gültig, sonst False
        """
        min_limit = MOTOR_LIMITS[motor_name].get("min", 0)
        max_limit = MOTOR_LIMITS[motor_name].get("max", 32767)
        if not (min_limit <= target_value <= max_limit):
            print(f"Zielwert {target_value} für Motor {motor_name} liegt außerhalb der Grenzen ({min_limit}, {max_limit}).")
            return False
        return True

controller = MotorControllerWithFocus()

slider_positions = [0, 100, 300, 450, 600, 750, 900, 750, 600, 600, 600, 300, 100, 0]
turntable_positions = [0, 45, 90, 180, 180, 270, 180, 180, 90, 180, 360, 90, 45, 0]

focus_enabled = True
camera_offset_z = 0

controller.initialize_focus(slider_positions, turntable_positions, duration=5, resolution=1000, focus_enabled=focus_enabled, camera_offset_z=camera_offset_z)

print("Kamera-Fokussteuerung abgeschlossen.")