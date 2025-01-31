import time
import numpy as np
from scipy.interpolate import CubicSpline
from src.dxl_manager import DynamixelManager
from src.settings import MOTOR_IDS, MOTOR_LIMITS, VELOCITY_LIMITS, CONVERSION_FACTORS, MOTOR_OFFSETS

class CameraSlider:
    def __init__(self):
        self.manager = DynamixelManager()
        self.motor_ids = MOTOR_IDS
        self.motor_limits = MOTOR_LIMITS
        self.velocity_limits = VELOCITY_LIMITS
        self.conversion_factors = CONVERSION_FACTORS
        self.motor_offsets = MOTOR_OFFSETS

    def smooth_acceleration(self, positions, duration, steps=100):
        """
        Erzeugt eine geglättete Beschleunigungskurve mit sanftem Start und Ende
        """
        t = np.linspace(0, duration, steps)
        # Verwende eine Cosinus-Funktion für sanfte Beschleunigung
        smooth_factor = (1 - np.cos(np.pi * t / duration)) / 2
        
        smoothed_positions = {}
        for motor in positions[0].keys():
            motor_positions = [pos[motor] for pos in positions]
            cs = CubicSpline(np.linspace(0, 1, len(motor_positions)), motor_positions)
            smoothed_positions[motor] = cs(smooth_factor)
            
        return [dict(zip(positions[0].keys(), pos)) for pos in zip(*smoothed_positions.values())]

    def move_motors(self, target_positions_list, velocity=None, acceleration=None, duration=10):
        """
        Verbesserte Version mit Bewegungsglättung
        """
        num_positions = len(target_positions_list)
        
        # Erhöhe die Anzahl der Zwischenschritte für flüssigere Bewegung
        interpolation_steps = max(num_positions * 10, 100)
        
        # Generiere geglättete Bewegungskurve
        smoothed_positions = self.smooth_acceleration(
            target_positions_list,
            duration,
            steps=interpolation_steps
        )
        
        step_duration = duration / interpolation_steps
        last_time = time.time()

        for target_positions in smoothed_positions:
            current_time = time.time()
            elapsed = current_time - last_time
            
            if elapsed < step_duration:
                time.sleep(max(0, step_duration - elapsed))
            
            goal_positions = {}
            for motor_name, target_position in target_positions.items():
                motor_id = self.motor_ids[motor_name]
                min_limit = self.motor_limits[motor_name]["min"]
                max_limit = self.motor_limits[motor_name]["max"]
                conversion = self.conversion_factors[motor_name]
                offset = self.motor_offsets.get(motor_name, 0)
                
                # Berechne Zielposition mit verbesserter Genauigkeit
                goal_position = (target_position + offset) / conversion
                goal_position = max(min(goal_position, max_limit), min_limit)
                goal_positions[motor_id] = int(goal_position)
            
            # Setze niedrigere Geschwindigkeit und Beschleunigung für sanftere Bewegung
            if velocity is not None:
                scaled_velocity = int(velocity * 0.8)  # 80% der ursprünglichen Geschwindigkeit
                self.manager.bulk_write_profile_velocity({motor_id: scaled_velocity for motor_id in self.motor_ids.values()})
            if acceleration is not None:
                scaled_acceleration = int(acceleration * 0.9)  # 60% der ursprünglichen Beschleunigung
                self.manager.bulk_write_profile_acceleration({motor_id: scaled_acceleration for motor_id in self.motor_ids.values()})
            
            self.manager.bulk_write_goal_positions(goal_positions)
            last_time = time.time()

    def read_positions(self):
        positions = self.manager.bulk_read_positions()
        converted_positions = {}
        for motor_name, motor_id in self.motor_ids.items():
            steps = positions.get(motor_id, 0)
            conversion = self.conversion_factors[motor_name]
            offset = self.motor_offsets.get(motor_name, 0)
            converted_positions[motor_name] = steps * conversion - offset
        return converted_positions

    def enable_motors(self):
        self.manager.enable_torque()

    def disable_motors(self):
        self.manager.disable_torque()

    def close(self):
        self.manager.close()

if __name__ == "__main__":
    slider = CameraSlider()
    slider.enable_motors()

    try:
        # Example: Move motors to multiple positions
        target_positions_list = [
            {"turntable": 0, "slider": 0, "pan": 0, "tilt": 0, "zoom": 0, "focus": 0},
            {"turntable": 45, "slider": 100, "pan": 45, "tilt": 45, "zoom": 45, "focus": 45},
            {"turntable": 90, "slider": 200, "pan": -90, "tilt": 0, "zoom": 90, "focus": 90},
            {"turntable": 135, "slider": 300, "pan": 135, "tilt": -45, "zoom": 135, "focus": 135},
            {"turntable": 180, "slider": 0, "pan": 160, "tilt": 50, "zoom": 180, "focus": 180}
        ]

        velocity = 8000  # units/s
        acceleration = 5000  # units/s^2
        duration = 200  # seconds

        slider.move_motors(target_positions_list, velocity, acceleration, duration)

        # Read and print current positions
        positions = slider.read_positions()
        print("Current positions:", positions)
    finally:
        slider.disable_motors()
        slider.close()
