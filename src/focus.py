import numpy as np
from math import atan2, degrees, radians, sqrt, cos, sin
from time import time
from collections import deque
from src.settings import (
    MOTOR_LIMITS, CONVERSION_FACTORS, MIN_FOCUS_DISTANCE, MAX_FOCUS_DISTANCE,
    DEFAULT_VELOCITY, DEFAULT_ACCELERATION, DEFAULT_DURATION
)

class FocusController:
    def __init__(self, object_position=(-400, 600, -300), history_size=5):
        self.object_x, self.object_y, self.object_z = object_position
        self.slider_position = 0  # Current position along Y-axis
        self.last_update_time = time()
        self.position_history = deque(maxlen=history_size)
        self.velocity = 0
        self.last_pan = 0
        self.last_tilt = 0
        self.last_focus = 0
        
    def update_velocity(self, current_pos):
        """
        Calculate current velocity based on position history
        """
        current_time = time()
        dt = current_time - self.last_update_time
        
        if dt > 0 and self.position_history:
            old_pos = self.position_history[0]
            self.velocity = (current_pos - old_pos) / dt
            
        self.position_history.append(current_pos)
        self.last_update_time = current_time
        
        return self.velocity
        
    def calculate_angles(self, slider_pos, prediction_time=0.02):
        """
        Calculate pan and tilt angles for a given slider position
        with prediction and smoothing
        """
        # Predict future position based on velocity
        predicted_pos = slider_pos + (self.velocity * prediction_time)
        
        # Calculate relative position from camera to object
        rel_x = self.object_x  # X stays constant
        rel_y = self.object_y - predicted_pos  # Y changes with slider position
        rel_z = self.object_z  # Z stays constant
        
        # Calculate pan angle (horizontal rotation) - inverted direction
        pan_angle = -degrees(atan2(rel_x, rel_y))
        
        # Calculate tilt angle (vertical rotation)
        distance_horizontal = sqrt(rel_x**2 + rel_y**2)
        tilt_angle = degrees(atan2(rel_z, distance_horizontal))
        
        # Apply smoothing
        smooth_factor = min(1.0, abs(self.velocity) / 100.0 + 0.3)  # Dynamic smoothing
        
        pan_angle = self.last_pan * (1 - smooth_factor) + pan_angle * smooth_factor
        tilt_angle = self.last_tilt * (1 - smooth_factor) + tilt_angle * smooth_factor
        
        self.last_pan = pan_angle
        self.last_tilt = tilt_angle
        
        return pan_angle, tilt_angle

    def calculate_focus(self, slider_pos, prediction_time=0.02):
        """
        Calculate focus value based on distance to object
        with prediction and smoothing
        """
        # Predict future position based on velocity
        predicted_pos = slider_pos + (self.velocity * prediction_time)
        
        # Calculate direct distance from camera to object
        rel_x = self.object_x
        rel_y = self.object_y - predicted_pos
        rel_z = self.object_z
        
        distance = sqrt(rel_x**2 + rel_y**2 + rel_z**2)
        
        # Convert distance to focus motor steps
        focus_min = MOTOR_LIMITS["focus"]["min"]
        focus_max = MOTOR_LIMITS["focus"]["max"]
        focus_range = focus_max - focus_min
        
        # Map distance to focus value using settings
        focus_value = ((distance - MIN_FOCUS_DISTANCE) / 
                      (MAX_FOCUS_DISTANCE - MIN_FOCUS_DISTANCE)) * focus_range + focus_min
        
        # Apply smoothing
        smooth_factor = min(1.0, abs(self.velocity) / 100.0 + 0.3)  # Dynamic smoothing
        focus_value = self.last_focus * (1 - smooth_factor) + focus_value * smooth_factor
        
        self.last_focus = focus_value
        return int(focus_value)

    def get_motor_positions(self, slider_pos, include_focus=True):
        """
        Get motor positions for a given slider position
        with velocity tracking and prediction.
        
        Args:
            slider_pos: Current slider position
            include_focus: Whether to include automatic focus calculation
        """
        # Update velocity tracking
        self.update_velocity(slider_pos)
        
        # Calculate positions with prediction
        pan_angle, tilt_angle = self.calculate_angles(slider_pos)
        
        positions = {
            "pan": pan_angle,
            "tilt": tilt_angle,
        }
        
        # Only include focus if requested
        if include_focus:
            positions["focus"] = self.calculate_focus(slider_pos)
            
        return positions

    def generate_movement_sequence(self, start_pos, end_pos, num_steps=50, include_focus=True):
        """
        Generate a sequence of motor positions for smooth movement
        
        Args:
            start_pos: Starting slider position
            end_pos: Ending slider position
            num_steps: Number of interpolation steps
            include_focus: Whether to include automatic focus calculation
        """
        slider_positions = np.linspace(start_pos, end_pos, num_steps)
        sequence = []
        
        for slider_pos in slider_positions:
            motor_positions = self.get_motor_positions(slider_pos, include_focus)
            sequence.append(motor_positions)
            
        return sequence

    def set_focus_position(self, focus_value):
        """
        Set a direct focus position value
        
        Args:
            focus_value: Raw focus position value
        Returns:
            Clamped focus value within valid range
        """
        focus_min = MOTOR_LIMITS["focus"]["min"]
        focus_max = MOTOR_LIMITS["focus"]["max"]
        return int(max(min(focus_value, focus_max), focus_min))

if __name__ == "__main__":
    from camera_slider import CameraSlider
    
    # Initialize both controllers
    focus_controller = FocusController(object_position=(-400, 600, -300))
    camera_slider = CameraSlider()
    
    try:
        # Enable motors
        camera_slider.enable_motors()
        
        # Example 1: Generate sequence with automatic focus
        print("\nExample 1: Automatic focus tracking")
        sequence = focus_controller.generate_movement_sequence(0, 900, num_steps=900, include_focus=True)
        
        movement_sequence = []
        for i, motors in enumerate(sequence):
            # Calculate slider position
            slider_pos = (600 / (len(sequence) - 1)) * i
            
            # Combine all motor positions
            position_dict = {
                "slider": slider_pos,
                "pan": motors["pan"],
                "tilt": motors["tilt"],
                "focus": motors.get("focus", 0),  # Use 0 if focus not included
                "turntable": 0,
                "zoom": 0
            }
            movement_sequence.append(position_dict)
        
        print("Starting movement with automatic focus...")
        print("Initial position:", movement_sequence[0])
        print("Final position:", movement_sequence[-1])
        
        camera_slider.move_motors(
            movement_sequence,
            velocity=DEFAULT_VELOCITY,
            acceleration=DEFAULT_ACCELERATION,
            duration=DEFAULT_DURATION
        )
        
        # Example 2: Manual focus control
        print("\nExample 2: Manual focus control")
        focus_position = focus_controller.set_focus_position(500)  # Set focus directly
        camera_slider.move_motors(
            [{"slider": 0, "pan": 0, "tilt": 0, "focus": focus_position}],
            velocity=DEFAULT_VELOCITY,
            acceleration=DEFAULT_ACCELERATION,
            duration=1
        )
        
        print("Starting movement sequence...")
        print("Initial position:", movement_sequence[0])
        print("Middle position:", movement_sequence[len(movement_sequence)//2])
        print("Final position:", movement_sequence[-1])
        
        # Execute the movement sequence using default settings
        camera_slider.move_motors(
            movement_sequence, 
            velocity=DEFAULT_VELOCITY,
            acceleration=DEFAULT_ACCELERATION,
            duration=DEFAULT_DURATION
        )
        
        # Read and print final positions
        final_positions = camera_slider.read_positions()
        print("\nFinal achieved positions:", final_positions)
        
    except Exception as e:
        print(f"Error during movement sequence: {e}")
    finally:
        camera_slider.disable_motors()
        camera_slider.close()
