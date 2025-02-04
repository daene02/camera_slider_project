import os
import json
from threading import Thread, Event
import time
from .motor_controller import motor_controller
from src.focus import FocusController
from src.settings import (
    MOTOR_IDS, PAN_TILT_VELOCITY, PAN_TILT_ACCELERATION,
    MOVEMENT_SETTINGS, DEFAULT_ACCELERATION
)
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
                        logger.error(f"Error verifying profile {f}: {str(e)}")
                        continue
            return profiles
        except Exception as e:
            logger.error(f"Error listing profiles: {str(e)}")
            return []

    def get_profile(self, name):
        try:
            profile_path = self.get_profile_path(name)
            if not os.path.exists(profile_path):
                return None
            with open(profile_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading profile: {str(e)}")
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
            logger.error(f"Error saving profile: {str(e)}")
            return False

    def verify_motor_positions(self, target_positions, tolerance=None):
        """Verify if motors have reached their target positions."""
        if tolerance is None:
            tolerance = MOVEMENT_SETTINGS['primary_motors']['position_tolerance']
            
        retry_count = 0
        max_retries = MOVEMENT_SETTINGS['primary_motors']['max_retries']
        check_interval = MOVEMENT_SETTINGS['primary_motors']['check_interval']
        
        while not self.playback_stop_event.is_set() and retry_count < max_retries:
            current_positions = motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_read_positions)
            if not current_positions:
                time.sleep(check_interval)
                retry_count += 1
                continue

            all_reached = True
            for motor_id, target in target_positions.items():
                # Skip if motor_id is pan or tilt if they're in the target positions
                if motor_id in [MOTOR_IDS['pan'], MOTOR_IDS['tilt']]:
                    continue
                    
                current = current_positions.get(motor_id, None)
                if current is None or abs(current - target) > tolerance:
                    all_reached = False
                    logger.debug(f"Motor {motor_id} not in position: current={current}, target={target}")
                    break

            if all_reached:
                logger.debug("Motors reached target positions")
                return True

            time.sleep(check_interval)
            retry_count += 1
            if retry_count % 20 == 0:
                logger.debug(f"Still waiting for motors to reach position... (attempt {retry_count}/{max_retries})")

        logger.warning("Position verification timed out or stopped")
        return False

    def get_focus_points(self):
        """Get focus points from the focus controller"""
        try:
            focus_controller = FocusController()
            return focus_controller.focus_points
        except Exception as e:
            logger.error(f"Error getting focus points: {str(e)}")
            return []

    def get_focus_point(self, point_id):
        """Get a specific focus point by ID"""
        try:
            focus_points = self.get_focus_points()
            for point in focus_points:
                if point['id'] == point_id:
                    return point
            logger.warning(f"Focus point not found: {point_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting focus point: {str(e)}")
            return None

    def run_profile(self, profile, settings):
        try:
            logger.info("Starting profile playback")
            
            # Set acceleration for primary motors
            acceleration = int(profile.get('acceleration', DEFAULT_ACCELERATION))
            primary_accel_dict = {
                MOTOR_IDS['turntable']: acceleration,
                MOTOR_IDS['slider']: acceleration,
                MOTOR_IDS['zoom']: acceleration,
                MOTOR_IDS['focus']: acceleration
            }
            motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_acceleration, primary_accel_dict)
            
            # Set fixed acceleration for pan/tilt
            pan_tilt_accel_dict = {
                MOTOR_IDS['pan']: PAN_TILT_ACCELERATION,
                MOTOR_IDS['tilt']: PAN_TILT_ACCELERATION
            }
            motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_acceleration, pan_tilt_accel_dict)

            # Process each point in sequence
            for i, point in enumerate(profile['points']):
                if self.playback_stop_event.is_set():
                    break

                try:
                    logger.debug(f"Processing point {i+1}")
                    
                    # Handle focus point first
                    focus_point_id = point.get('focus_point_id')
                    if focus_point_id is not None:
                        focus_point = self.get_focus_point(focus_point_id)
                        if focus_point:
                            logger.debug(f"Setting focus point: {focus_point}")
                            # Create new FocusController with the focus point coordinates
                            self.focus_controller = FocusController(
                                object_position=(focus_point['x'], focus_point['y'], focus_point['z'])
                            )
                    
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
                    logger.debug(f"Setting motor velocities: {primary_velocity_dict}")
                    motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_velocity, primary_velocity_dict)
                    
                    logger.debug(f"Moving to positions: {positions}")
                    if not motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_goal_positions, positions):
                        raise Exception(f"Failed to move primary motors at point {i+1}")

                    # Handle focus tracking after primary motors move
                    if self.focus_controller:
                        try:
                            slider_pos = motor_controller.steps_to_units(positions[MOTOR_IDS['slider']], 'slider')
                            motor_positions = self.focus_controller.get_motor_positions(slider_pos)
                            
                            pan_tilt_positions = {
                                MOTOR_IDS['pan']: motor_controller.units_to_steps(motor_positions['pan'], 'pan'),
                                MOTOR_IDS['tilt']: motor_controller.units_to_steps(motor_positions['tilt'], 'tilt')
                            }
                            
                            logger.debug(f"Setting pan/tilt positions: {pan_tilt_positions}")
                            
                            # Set velocity and move pan/tilt motors
                            pan_tilt_velocity = {
                                MOTOR_IDS['pan']: PAN_TILT_VELOCITY,
                                MOTOR_IDS['tilt']: PAN_TILT_VELOCITY
                            }
                            motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_velocity, pan_tilt_velocity)
                            motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_goal_positions, pan_tilt_positions)
                            
                        except Exception as e:
                            logger.error(f"Focus tracking error at point {i+1}: {str(e)}")
                            continue

                    # Wait for primary motors to reach their positions
                    if not self.verify_motor_positions(positions):
                        logger.warning(f"Primary motors didn't reach target positions at point {i+1}, continuing...")

                except Exception as e:
                    logger.error(f"Error processing point {i+1}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in profile playback: {str(e)}")
        finally:
            self.focus_controller = None
            self.playback_stop_event.clear()

    def start_playback(self, profile, settings):
        if self.current_playback_thread and self.current_playback_thread.is_alive():
            return False, "Playback already in progress"
            
        try:
            self.playback_stop_event.clear()
            self.focus_controller = None
            self.current_playback_thread = Thread(target=self.run_profile, args=(profile, settings))
            self.current_playback_thread.start()
            return True, None
        except Exception as e:
            return False, str(e)

    def stop_playback(self):
        try:
            self.playback_stop_event.set()
            self.focus_controller = None
            current_positions = motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_read_positions)
            if current_positions:
                motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_goal_positions, current_positions)
            return True, None
        except Exception as e:
            return False, str(e)

profile_controller = ProfileController()
