import os
import json
from threading import Thread, Event
import time
from .motor_controller import motor_controller, MOTOR_IDS
from src.focus import FocusController

class ProfileController:
    # Constants for pan/tilt control
    PAN_TILT_VELOCITY = 20
    PAN_TILT_ACCELERATION = 20
    POSITION_CHECK_TIMEOUT = 30  # seconds - increased from 10s to 30s
    POSITION_CHECK_INTERVAL = 0.05  # seconds

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
            # Filter out pan/tilt positions from each point
            if 'points' in profile_data:
                for point in profile_data['points']:
                    if 'positions' in point:
                        # Remove pan and tilt positions if they exist
                        positions = {
                            k: v for k, v in point['positions'].items()
                            if k not in [str(MOTOR_IDS['pan']), str(MOTOR_IDS['tilt'])]
                        }
                        point['positions'] = positions

            profile_path = self.get_profile_path(profile_data['name'])
            with open(profile_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving profile: {str(e)}")
            return False

    def wait_for_time(self, duration):
        """Wait for specified time while checking for stop event."""
        start_time = time.time()
        while not self.playback_stop_event.is_set():
            if time.time() - start_time >= duration:
                return True
            time.sleep(self.POSITION_CHECK_INTERVAL)
        return False

    def run_profile(self, profile, settings):
        try:
            # Set drive mode to time-based profile (write value 4 to address 10)
            drive_mode_dict = {
                MOTOR_IDS['turntable']: 4,
                MOTOR_IDS['slider']: 4,
                MOTOR_IDS['zoom']: 4,
                MOTOR_IDS['focus']: 4,
                MOTOR_IDS['pan']: 4,
                MOTOR_IDS['tilt']: 4
            }
            if not motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_drive_mode, drive_mode_dict):
                raise Exception("Failed to set drive mode")

            # Set acceleration for primary motors
            acceleration = int(profile.get('acceleration', 1800))
            primary_accel_dict = {
                MOTOR_IDS['turntable']: acceleration,
                MOTOR_IDS['slider']: acceleration,
                MOTOR_IDS['zoom']: acceleration,
                MOTOR_IDS['focus']: acceleration
            }
            motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_acceleration, primary_accel_dict)
            
            # Set fixed acceleration for pan/tilt
            pan_tilt_accel_dict = {
                MOTOR_IDS['pan']: self.PAN_TILT_ACCELERATION,
                MOTOR_IDS['tilt']: self.PAN_TILT_ACCELERATION
            }
            motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_acceleration, pan_tilt_accel_dict)

            # Initialize/reinitialize focus controller
            self.focus_controller = FocusController(object_position=(400, 600, -300))

            # Process each point in sequence
            for i, point in enumerate(profile['points']):
                if self.playback_stop_event.is_set():
                    break

                try:
                    # Get the time-based velocity (duration) from the point
                    duration = int(point.get('velocity', 1000))
                    
                    # Convert saved positions to motor steps (explicitly exclude pan/tilt)
                    positions = {
                        int(motor_id): int(pos) 
                        for motor_id, pos in point['positions'].items() 
                        if str(motor_id) not in [str(MOTOR_IDS['pan']), str(MOTOR_IDS['tilt'])]
                    }

                    # Set velocity and positions for primary motors together
                    primary_velocity_dict = {
                        MOTOR_IDS['turntable']: duration,
                        MOTOR_IDS['slider']: duration,
                        MOTOR_IDS['zoom']: duration,
                        MOTOR_IDS['focus']: duration
                    }
                    motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_velocity, primary_velocity_dict)
                    if not motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_goal_positions, positions):
                        raise Exception(f"Failed to move primary motors at point {i+1}")

                    print(f"Moving to point {i+1}, duration: {duration}")  # Debug info
                    print(f"Primary positions: {positions}")  # Debug info

                    # Wait for the specified duration
                    if not self.wait_for_time(duration/1000.0):  # Convert to seconds
                        raise Exception(f"Movement stopped during point {i+1}")

                    # Calculate and verify pan/tilt positions
                    try:
                        slider_pos = motor_controller.steps_to_units(positions[MOTOR_IDS['slider']], 'slider')
                        motor_positions = self.focus_controller.get_motor_positions(slider_pos)
                        
                        pan_tilt_positions = {
                            MOTOR_IDS['pan']: motor_controller.units_to_steps(motor_positions['pan'], 'pan'),
                            MOTOR_IDS['tilt']: motor_controller.units_to_steps(motor_positions['tilt'], 'tilt')
                        }
                        
                        print(f"Pan/tilt positions: {pan_tilt_positions}")  # Debug info
                        
                        # Set velocity and move pan/tilt motors
                        pan_tilt_velocity = {
                            MOTOR_IDS['pan']: 50,  # Use same duration as primary motors
                            MOTOR_IDS['tilt']: 50
                        }
                        motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_velocity, pan_tilt_velocity)
                        if not motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_goal_positions, pan_tilt_positions):
                            raise Exception(f"Failed to move pan/tilt motors at point {i+1}")
                        
                        # Wait for the specified duration
                       # if not self.wait_for_time(duration/1000.0):  # Convert to seconds
                           # raise Exception(f"Pan/tilt movement stopped during point {i+1}")
                            
                    except Exception as e:
                        print(f"Focus tracking error at point {i+1}: {str(e)}")
                        # Continue with next point even if focus tracking fails
                        continue

                except Exception as e:
                    print(f"Error processing point {i+1}: {str(e)}")
                    # Continue with next point if there's an error
                    continue

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
