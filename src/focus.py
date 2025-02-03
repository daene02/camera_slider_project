import numpy as np
from math import atan2, degrees, radians, sqrt, cos, sin
from src.settings import (
    MOTOR_LIMITS, CONVERSION_FACTORS, MIN_FOCUS_DISTANCE, MAX_FOCUS_DISTANCE,
    DEFAULT_VELOCITY, DEFAULT_ACCELERATION, DEFAULT_DURATION
)

class FocusController:
    def __init__(self, object_position=(-400, 600, -300)):
        self.object_x, self.object_y, self.object_z = object_position
        self.slider_position = 0  # Current position along Y-axis
        
    def calculate_angles(self, slider_pos):
        """
        Calculate pan and tilt angles for a given slider position
        to keep the object centered in frame
        """
        # Calculate relative position from camera to object
        rel_x = self.object_x  # X stays constant
        rel_y = self.object_y - slider_pos  # Y changes with slider position
        rel_z = self.object_z  # Z stays constant
        
        # Calculate pan angle (horizontal rotation) - inverted direction
        pan_angle = -degrees(atan2(rel_x, rel_y))  # Added minus sign to invert direction
        
        # Calculate tilt angle (vertical rotation)
        distance_horizontal = sqrt(rel_x**2 + rel_y**2)
        tilt_angle = degrees(atan2(rel_z, distance_horizontal))
        
        return pan_angle, tilt_angle

    def calculate_focus(self, slider_pos):
        """
        Calculate focus value based on distance to object
        """
        # Calculate direct distance from camera to object
        rel_x = self.object_x
        rel_y = self.object_y - slider_pos
        rel_z = self.object_z
        
        distance = sqrt(rel_x**2 + rel_y**2 + rel_z**2)
        
        # Convert distance to focus motor steps (this needs to be calibrated)
        # Assuming linear relationship between distance and focus value
        focus_min = MOTOR_LIMITS["focus"]["min"]
        focus_max = MOTOR_LIMITS["focus"]["max"]
        focus_range = focus_max - focus_min
        
        # Map distance to focus value using settings
        focus_value = ((distance - MIN_FOCUS_DISTANCE) / (MAX_FOCUS_DISTANCE - MIN_FOCUS_DISTANCE)) * focus_range + focus_min
        return int(focus_value)

    def get_motor_positions(self, slider_pos):
        """
        Get all motor positions for a given slider position
        """
        pan_angle, tilt_angle = self.calculate_angles(slider_pos)
        focus_value = self.calculate_focus(slider_pos)
        
        return {
            "pan": pan_angle,
            "tilt": tilt_angle,
            "focus": focus_value
        }

    def generate_movement_sequence(self, start_pos, end_pos, num_steps=50):
        """
        Generate a sequence of motor positions for smooth movement
        """
        slider_positions = np.linspace(start_pos, end_pos, num_steps)
        sequence = []
        
        for slider_pos in slider_positions:
            motor_positions = self.get_motor_positions(slider_pos)
            sequence.append(motor_positions)
            
        return sequence

if __name__ == "__main__":
    from camera_slider import CameraSlider
    
    # Initialize both controllers
    focus_controller = FocusController(object_position=(-400, 600, -300))
    camera_slider = CameraSlider()
    
    try:
        # Enable motors
        camera_slider.enable_motors()
        
        # Generate a sequence of positions as the slider moves from 0 to 600mm
        sequence = focus_controller.generate_movement_sequence(0, 900, num_steps=900)
        
        # Create full movement sequence including slider positions
        movement_sequence = []
        for i, motors in enumerate(sequence):
            # Calculate slider position
            slider_pos = (600 / (len(sequence) - 1)) * i
            
            # Combine all motor positions
            position_dict = {
                "slider": slider_pos,
                "pan": motors["pan"],
                "tilt": motors["tilt"],
                "focus": motors["focus"],
                "turntable": 0,  # Static position for turntable
                "zoom": 0        # Static position for zoom
            }
            movement_sequence.append(position_dict)
        
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
