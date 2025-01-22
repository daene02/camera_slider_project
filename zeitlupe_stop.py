from motor_control import MotorController
from settings import MOTOR_IDS, CONVERSION_FACTORS, TURNTABLE_POSITION, PID_DEFAULTS, MOTOR_OFFSETS, MOTOR_LIMITS, PROFILE_VELOCITY, PROFILE_ACCELERATION, LEN_PRO_GOAL_POSITION, LEN_PRO_PRESENT_POSITION
import math
import numpy as np
from scipy.interpolate import CubicSpline
import time
import os
import sys

VELOCITY_LIMITS = {
    "turntable": 1800,
    "slider": 2000,
    "pan": 1800,
    "tilt": 1800
}

class MotorControllerWithFocus(MotorController):
    def calculate_focus_angles(self, slider_position, x_offset, y_offset, z_offset, camera_offset_z=0):
        relative_x = x_offset #+ TURNTABLE_POSITION.get("offset", 0) * math.cos(math.radians(y_offset))
        relative_y = y_offset #- slider_position #+ TURNTABLE_POSITION.get("offset", 0) * math.sin(math.radians(y_offset))
        relative_z = z_offset# - MOTOR_OFFSETS.get("camera_to_tilt_pivot", 0) - camera_offset_z

        pan_angle = math.degrees(math.atan2(relative_x, relative_y)) + MOTOR_OFFSETS.get("pan", 0)
        tilt_angle = math.degrees(math.atan2(relative_z, math.sqrt(relative_x**2 + relative_y**2))) + MOTOR_OFFSETS.get("tilt", 0)

        return pan_angle, tilt_angle

    def smooth_trajectory(self, positions, resolution=3000):
        x = np.linspace(0, len(positions["slider"]) - 1, len(positions["slider"]))
        smoothed = {}

        for axis, values in positions.items():
            spline = CubicSpline(x, values)
            smoothed[axis] = spline(np.linspace(0, len(positions["slider"]) - 1, resolution))

        return smoothed

    def validate_target_steps(self, motor_name, target_steps):
        min_limit = MOTOR_LIMITS[motor_name]["min"]
        max_limit = MOTOR_LIMITS[motor_name]["max"]
        if not (min_limit <= target_steps <= max_limit):
            print(f"Zielposition {target_steps} für Motor {motor_name} liegt außerhalb der Grenzen ({min_limit}, {max_limit}).")
            return False
        return True

    def set_profile(self, motor_id, velocity, acceleration):
        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, PROFILE_VELOCITY, int(velocity))
        if result != 0 or error != 0:
            raise Exception(f"Fehler beim Setzen der Geschwindigkeit für Motor {motor_id}: result={result}, error={error}")

        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, PROFILE_ACCELERATION, int(acceleration))
        if result != 0 or error != 0:
            raise Exception(f"Fehler beim Setzen der Beschleunigung für Motor {motor_id}: result={result}, error={error}")

    def bulk_read_positions(self):
        positions = super().bulk_read_positions(list(MOTOR_IDS.values()))
        print("[DEBUG] Bulk read positions:", positions)
        mapped_positions = {motor: positions.get(MOTOR_IDS[motor], None) for motor in MOTOR_IDS}
        print("[DEBUG] Mapped positions:", mapped_positions)
        return mapped_positions

    def bulk_write_positions(self, target_positions):
        formatted_positions = {MOTOR_IDS[motor]: target_positions[motor] for motor in target_positions}
        print("[DEBUG] Bulk write positions:", formatted_positions)
        super().bulk_write_positions(formatted_positions)

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
                conversion_factor = CONVERSION_FACTORS[motor_name]
                target_steps = int(position / conversion_factor)

                if not self.validate_target_steps(motor_name, target_steps):
                    continue

                velocity = abs(position - current_positions[motor_name]) / step_duration
                velocity_steps = min(int(velocity / conversion_factor), VELOCITY_LIMITS[motor_name])

                print(f"Motor: {motor_name}, Ziel: {position}, Geschwindigkeit: {velocity_steps}")
                self.set_profile(MOTOR_IDS[motor_name], velocity_steps, acceleration=500)
                target_positions[motor_name] = target_steps

            self.bulk_write_positions(target_positions)
            time.sleep(step_duration)

    def correct_motor_position(self, motor_id, target_position, tolerance=0.5):
        current_positions = self.bulk_read_positions()
        motor_name = next(name for name, id in MOTOR_IDS.items() if id == motor_id)
        conversion_factor = CONVERSION_FACTORS[motor_name]
        actual_position = current_positions[motor_name] * conversion_factor

        if abs(actual_position - target_position) > tolerance:
            target_steps = int(target_position / conversion_factor)
            if not self.validate_target_steps(motor_name, target_steps):
                return

            print(f"Korrigiere Position: Motor ID={motor_id}, Soll={target_position}, Ist={actual_position}, Ziel in Schritten={target_steps}")
            self.set_goal_position(motor_id, target_steps)

    def synchronize_focus_movements(self, slider_positions, turntable_position, camera_offset_z=0):
        pan_positions = []
        tilt_positions = []

        for slider_position in slider_positions:
            pan_angle, tilt_angle = self.calculate_focus_angles(
                slider_position,
                turntable_position["x"],
                turntable_position["y"],
                turntable_position["z"],
                camera_offset_z=camera_offset_z
            )
            pan_positions.append(pan_angle)
            tilt_positions.append(tilt_angle)

        return pan_positions, tilt_positions

    def move_with_focus(self, slider_positions, turntable_positions, duration=10, resolution=3000, focus_enabled=False, camera_offset_z=0):
        if focus_enabled:
            print("Fokusmodus aktiviert: Berechne Pan- und Tilt-Winkel...")
            pan_positions, tilt_positions = self.synchronize_focus_movements(slider_positions, TURNTABLE_POSITION, camera_offset_z=camera_offset_z)
        else:
            print("Normale Steuerung: Pan und Tilt bleiben unverändert.")
            pan_positions = [0] * len(slider_positions)
            tilt_positions = [0] * len(slider_positions)

        positions = {
            "slider": slider_positions,
            "pan": pan_positions,
            "tilt": tilt_positions,
            "turntable": turntable_positions
        }

        smoothed_positions = self.smooth_trajectory(positions, resolution=resolution)
        self.synchronize_movements(smoothed_positions, resolution=resolution, duration=duration)

    def initialize_focus(self, slider_positions, turntable_positions, duration=10, resolution=3000, focus_enabled=False, camera_offset_z=0):
        print("Initialisiere Fokusmodus...")
        current_positions = self.bulk_read_positions()

        if "slider" not in current_positions or current_positions["slider"] is None:
            raise KeyError("Fehler: Aktuelle Position des Sliders konnte nicht gelesen werden.")

        initial_positions = {
            "slider": [current_positions["slider"]] + slider_positions,
            "turntable": [current_positions["turntable"]] + turntable_positions,
            "pan": [current_positions["pan"]],
            "tilt": [current_positions["tilt"]]
        }

        self.move_with_focus(initial_positions["slider"], initial_positions["turntable"], duration, resolution, focus_enabled, camera_offset_z)

controller = MotorControllerWithFocus()

slider_positions = [0, 100, 300, 450, 600, 750, 900, 750, 600, 600, 600, 300, 100, 0]
turntable_positions = [0, 45, 90, 180, 180, 270, 180, 180, 90, 180, 360, 90, 45, 0]

focus_enabled = True
camera_offset_z = MOTOR_OFFSETS.get("camera_to_tilt_pivot", 0)

controller.initialize_focus(slider_positions, turntable_positions, duration=5, resolution=800, focus_enabled=focus_enabled, camera_offset_z=camera_offset_z)

print("Kamera-Fokussteuerung abgeschlossen.")
