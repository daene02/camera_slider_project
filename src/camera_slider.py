import time
import numpy as np
from scipy.interpolate import CubicSpline
from threading import Thread, Event
from src.dxl_manager import DynamixelManager
from src.motion.motion_predictor import MotionPredictor
from src.settings import (
    MOTOR_IDS, MOTOR_LIMITS, VELOCITY_LIMITS, 
    CONVERSION_FACTORS, MOTOR_OFFSETS, MOTION_CONTROL
)

class CameraSlider:
    def __init__(self):
        self.manager = DynamixelManager()
        self.motor_ids = MOTOR_IDS
        self.motor_limits = MOTOR_LIMITS
        self.velocity_limits = VELOCITY_LIMITS
        self.conversion_factors = CONVERSION_FACTORS
        self.motor_offsets = MOTOR_OFFSETS
        self.update_rate = 100  # 100Hz update rate
        self.stop_event = Event()
        self.movement_thread = None
        
        # Initialize motion prediction
        self.motion_predictor = MotionPredictor()
        self.focus_mode = False
        
        # Enable motion prediction by default for pan/tilt
        self.motion_predictor.enable_focus_mode(True)
        # Initialize with the center position
        self.motion_predictor.set_focus_point({
            "x": 400,  # Center X
            "y": 600,  # Center Y 
            "z": -300  # Center Z
        })

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

    def _movement_loop(self, smoothed_positions, step_duration, velocity, acceleration):
        """
        High-frequency movement loop running in separate thread with motion prediction
        """
        last_time = time.time()
        next_update = last_time + (1.0 / self.update_rate)

        # Calculate total duration for profile-based prediction
        total_duration = len(smoothed_positions) * step_duration

        for target_positions in smoothed_positions:
            if self.stop_event.is_set():
                break

            current_time = time.time()
            
            # Precise timing control
            if current_time < next_update:
                time.sleep(max(0, next_update - current_time))
                
            # Get current positions and velocities
            current_positions = self.read_positions()
            current_velocities = {
                name: (target_positions[name] - current_positions[name]) / step_duration
                for name in ['slider', 'pan', 'tilt']
            }
            
            # Update motion prediction
            predicted_state = self.motion_predictor.update(
                measurements=current_positions,
                velocities=current_velocities,
                profile_duration=total_duration
            )
            
            # Use predicted positions for pan/tilt if in focus mode
            if self.focus_mode:
                target_positions['pan'] = predicted_state.pan_angle
                target_positions['tilt'] = predicted_state.tilt_angle
            
            # Convert positions to motor units
            goal_positions = {}
            for motor_name, target_position in target_positions.items():
                motor_id = self.motor_ids[motor_name]
                min_limit = self.motor_limits[motor_name]["min"]
                max_limit = self.motor_limits[motor_name]["max"]
                conversion = self.conversion_factors[motor_name]
                offset = self.motor_offsets.get(motor_name, 0)
                
                # Enhanced position calculation
                goal_position = (target_position + offset) / conversion
                goal_position = max(min(goal_position, max_limit), min_limit)
                goal_positions[motor_id] = int(goal_position)
            
            # Dynamic velocity scaling based on movement size
            if velocity is not None:
                current_positions = self.read_positions()
                max_diff = max(abs(current_positions[k] - target_positions[k]) 
                             for k in current_positions.keys())
                scale = min(1.0, max_diff / 100)  # Scale based on movement size
                scaled_velocity = int(velocity * (0.7 + scale * 0.3))  # 70-100% of original velocity
                self.manager.bulk_write_profile_velocity({motor_id: scaled_velocity for motor_id in self.motor_ids.values()})
            
            # Adaptive acceleration
            if acceleration is not None:
                scaled_acceleration = int(acceleration * 0.9)
                self.manager.bulk_write_profile_acceleration({motor_id: scaled_acceleration for motor_id in self.motor_ids.values()})
            
            self.manager.bulk_write_goal_positions(goal_positions)
            
            next_update = current_time + (1.0 / self.update_rate)

    def move_motors(self, target_positions_list, velocity=None, acceleration=None, duration=10, focus_point=None):
        """
        Enhanced version with high-frequency updates and smooth motion
        """
        # Update focus point if provided
        if focus_point is not None:
            self.motion_predictor.set_focus_point(focus_point)
            self.motion_predictor.enable_focus_mode(True)
            self.focus_mode = True
        
        # Stop any existing movement
        self.stop_event.set()
        if self.movement_thread and self.movement_thread.is_alive():
            self.movement_thread.join()
        self.stop_event.clear()
        
        num_positions = len(target_positions_list)
        interpolation_steps = int(self.update_rate * duration)  # Match steps to update rate
        
        # Generate smoothed movement curve
        smoothed_positions = self.smooth_acceleration(
            target_positions_list,
            duration,
            steps=interpolation_steps
        )
        
        step_duration = duration / interpolation_steps
        
        # Start movement thread
        self.movement_thread = Thread(
            target=self._movement_loop,
            args=(smoothed_positions, step_duration, velocity, acceleration)
        )
        self.movement_thread.start()

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
        self.stop_event.set()
        if self.movement_thread and self.movement_thread.is_alive():
            self.movement_thread.join()
        self.motion_predictor.enable_focus_mode(False)
        self.focus_mode = False
        self.manager.close()
        
    def set_focus_mode(self, enable: bool):
        """Enable or disable focus tracking mode"""
        self.focus_mode = enable
        self.motion_predictor.enable_focus_mode(enable)

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

        velocity = 10000  # units/s
        acceleration = 1800  # units/s^2
        duration = 100  # seconds

        slider.move_motors(target_positions_list, velocity, acceleration, duration)

        # Read and print current positions
        positions = slider.read_positions()
        print("Current positions:", positions)
    finally:
        slider.disable_motors()
        slider.close()
