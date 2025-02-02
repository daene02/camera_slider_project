import os
import json
from threading import Thread, Event
import time
from .motor_controller import motor_controller, MOTOR_IDS
from src.focus import FocusController

class ProfileController:
    def __init__(self):
        self.playback_stop_event = Event()
        self.current_playback_thread = None
        self.focus_controller = None

    def get_profile_path(self, name=None):
        current_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        profile_dir = os.path.join(current_dir, 'profiles')
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        return os.path.join(profile_dir, f'{name}.json') if name else profile_dir

    def list_profiles(self):
        try:
            profile_dir = self.get_profile_path()
            profiles = []
            for f in os.listdir(profile_dir):
                if f.endswith('.json') and f != 'focus_points.json':
                    profile_name = f[:-5]
                    try:
                        with open(os.path.join(profile_dir, f), 'r') as file:
                            json.load(file)  # Verify JSON is valid
                        profiles.append(profile_name)
                    except Exception as e:
                        print(f"Error verifying profile {f}: {str(e)}")
                        continue
            return profiles
        except Exception as e:
            print(f"Error listing profiles: {str(e)}")
            return []

    def get_profile(self, name):
        try:
            profile_path = self.get_profile_path(name)
            if not os.path.exists(profile_path):
                return None
            with open(profile_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading profile: {str(e)}")
            return None

    def save_profile(self, profile_data):
        try:
            profile_path = self.get_profile_path(profile_data['name'])
            with open(profile_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving profile: {str(e)}")
            return False

    def run_profile(self, profile, settings):
        try:
            # Set acceleration for primary motors
            acceleration = int(profile.get('acceleration', 1800))
            primary_accel_dict = {
                MOTOR_IDS['turntable']: acceleration,
                MOTOR_IDS['slider']: acceleration,
                MOTOR_IDS['zoom']: acceleration,
                MOTOR_IDS['focus']: acceleration
            }
            motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_acceleration, primary_accel_dict)
            
            # Set acceleration for pan/tilt (slightly lower for smoother movement)
            pan_tilt_accel = int(acceleration =50)  # 80% of primary acceleration
            pan_tilt_accel_dict = {
                MOTOR_IDS['pan']: pan_tilt_accel,
                MOTOR_IDS['tilt']: pan_tilt_accel
            }
            motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_acceleration, pan_tilt_accel_dict)

            # Initialize focus controller for auto-calculated pan/tilt
            if self.focus_controller is None:
                self.focus_controller = FocusController(object_position=(400, 600, -300))

            # Process each point in sequence
            for point in profile['points']:
                if self.playback_stop_event.is_set():
                    break

                # Set velocity for primary motors
                velocity = int(point.get('velocity', 1000))
                primary_velocity_dict = {
                    MOTOR_IDS['turntable']: velocity,
                    MOTOR_IDS['slider']: velocity,
                    MOTOR_IDS['zoom']: velocity,
                    MOTOR_IDS['focus']: velocity
                }
                motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_velocity, primary_velocity_dict)

                # Convert saved positions to motor steps (excludes pan/tilt)
                positions = {int(motor_id): int(pos) for motor_id, pos in point['positions'].items()}
                
                # Move primary motors first
                motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_goal_positions, positions)
                
                # Calculate pan/tilt positions based on current slider position
                slider_pos = motor_controller.steps_to_units(positions[MOTOR_IDS['slider']], 'slider')
                motor_positions = self.focus_controller.get_motor_positions(slider_pos)
                
                # Pan/tilt velocity (slightly higher for smooth tracking)
                pan_tilt_velocity = {
                    MOTOR_IDS['pan']: int(velocity =50),
                    MOTOR_IDS['tilt']: int(velocity =50)
                }
                motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_velocity, pan_tilt_velocity)
                
                # Prepare and execute pan/tilt movement separately
                pan_tilt_positions = {
                    MOTOR_IDS['pan']: motor_controller.units_to_steps(motor_positions['pan'], 'pan'),
                    MOTOR_IDS['tilt']: motor_controller.units_to_steps(motor_positions['tilt'], 'tilt')
                }
                motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_goal_positions, pan_tilt_positions)
                
                # Wait for position to be reached
                while not self.playback_stop_event.is_set():
                    current_positions = motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_read_positions)
                    if not current_positions:
                        time.sleep(0.05)
                        continue

                    # Check primary motors position
                    primary_reached = True
                    for motor_id, target_pos in positions.items():
                        current_pos = current_positions.get(motor_id, 0)
                        if abs(current_pos - target_pos) >= 5:
                            primary_reached = False
                            break
                    
                    # Check pan/tilt position
                    pan_tilt_reached = True
                    for motor_id, target_pos in pan_tilt_positions.items():
                        current_pos = current_positions.get(motor_id, 0)
                        if abs(current_pos - target_pos) >= 10:  # Larger tolerance for pan/tilt
                            pan_tilt_reached = True
                            time.sleep(1)
                    
                    if primary_reached and pan_tilt_reached:
                        break
                    
                    time.sleep(0.05)
                
        except Exception as e:
            print(f"Error in profile playback: {str(e)}")
        finally:
            self.playback_stop_event.clear()

    def start_playback(self, profile, settings):
        if self.current_playback_thread and self.current_playback_thread.is_alive():
            return False, "Playback already in progress"
            
        try:
            self.playback_stop_event.clear()
            self.current_playback_thread = Thread(target=self.run_profile, args=(profile, settings))
            self.current_playback_thread.start()
            return True, None
        except Exception as e:
            return False, str(e)

    def stop_playback(self):
        try:
            self.playback_stop_event.set()
            current_positions = motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_read_positions)
            if current_positions:
                motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_goal_positions, current_positions)
            return True, None
        except Exception as e:
            return False, str(e)

profile_controller = ProfileController()
