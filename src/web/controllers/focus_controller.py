import os
import json
from threading import Thread, Event
import time
from src.focus import FocusController as BaseFocusController
from .motor_controller import motor_controller, MOTOR_IDS

class FocusController:
    def __init__(self):
        self.tracking_stop_event = Event()
        self.current_tracking_thread = None
        self.focus_controller = None
        self.focus_points = []
        self.load_focus_points()

    def get_focus_points_path(self):
        current_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(current_dir, 'profiles', 'focus_points.json')

    def load_focus_points(self):
        try:
            path = self.get_focus_points_path()
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self.focus_points = json.load(f)
            print("Loaded focus points:", self.focus_points)
        except Exception as e:
            print(f"Error loading focus points: {str(e)}")
            self.focus_points = []

    def save_focus_points(self):
        try:
            path = self.get_focus_points_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(self.focus_points, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving focus points: {str(e)}")
            return False

    def add_focus_point(self, point):
        if all(k in point for k in ('x', 'y', 'z')):
            self.focus_points.append(point)
            self.save_focus_points()
            return True
        return False

    def remove_focus_point(self, index):
        if 0 <= index < len(self.focus_points):
            self.focus_points.pop(index)
            self.save_focus_points()
            return True
        return False

    def get_focus_point(self, index):
        if 0 <= index < len(self.focus_points):
            return self.focus_points[index]
        return None

    def verify_motor_positions(self, target_positions, current_positions, tolerance=5):
        """Verify if motors reached their target positions within tolerance"""
        for motor_id, target in target_positions.items():
            if motor_id not in current_positions:
                continue
            if abs(target - current_positions[motor_id]) > tolerance:
                return False
        return True

    def track_focus_point(self, point):
        if self.focus_controller is None:
            self.focus_controller = BaseFocusController(object_position=(point['x'], point['y'], point['z']))
        else:
            self.focus_controller.object_x = point['x']
            self.focus_controller.object_y = point['y']
            self.focus_controller.object_z = point['z']

        try:
            motor_controller.toggle_torque(enable=True)
            last_update_time = 0
            update_interval = 0.02  # 50Hz update rate
            
            while not self.tracking_stop_event.is_set():
                current_time = time.time()
                
                # Throttle updates to prevent overwhelming the motors
                if current_time - last_update_time < update_interval:
                    time.sleep(0.001)  # Small sleep to prevent CPU hogging
                    continue
                
                positions = motor_controller.get_motor_positions()
                if not positions:
                    time.sleep(0.01)
                    continue
                
                # Get current slider position in mm
                try:
                    slider_pos = motor_controller.steps_to_units(positions[MOTOR_IDS['slider']], 'slider')
                except KeyError:
                    print("Error: Slider motor ID not found")
                    continue
                except Exception as e:
                    print(f"Error converting slider position: {str(e)}")
                    continue
                
                try:
                    # Calculate motor positions for current slider position
                    motor_positions = self.focus_controller.get_motor_positions(slider_pos)
                    
                    # Convert angles to steps
                    target_positions = {
                        MOTOR_IDS['pan']: motor_controller.units_to_steps(motor_positions['pan'], 'pan'),
                        MOTOR_IDS['tilt']: motor_controller.units_to_steps(motor_positions['tilt'], 'tilt'),
                        MOTOR_IDS['focus']: motor_controller.units_to_steps(motor_positions['focus'], 'focus')
                    }
                    
                    # Verify current positions are within acceptable range
                    if not self.verify_motor_positions(target_positions, positions):
                        motor_controller.safe_dxl_operation(
                            motor_controller.dxl.bulk_write_goal_positions, 
                            target_positions
                        )
                    
                    last_update_time = current_time
                    
                except Exception as e:
                    print(f"Error during position calculation: {str(e)}")
                    time.sleep(0.1)  # Brief pause on error before retrying
                    continue
                
        except Exception as e:
            print(f"Error during focus tracking: {str(e)}")
        finally:
            self.tracking_stop_event.clear()
            motor_controller.toggle_torque(enable=False)

    def start_tracking(self, point):
        if self.current_tracking_thread and self.current_tracking_thread.is_alive():
            return False, "Tracking already in progress"

        if not all(k in point for k in ('x', 'y', 'z')):
            return False, "Invalid point data"
            
        try:
            self.tracking_stop_event.clear()
            self.current_tracking_thread = Thread(target=self.track_focus_point, args=(point,))
            self.current_tracking_thread.start()
            return True, None
        except Exception as e:
            return False, str(e)

    def stop_tracking(self):
        self.tracking_stop_event.set()
        return True

focus_controller = FocusController()
