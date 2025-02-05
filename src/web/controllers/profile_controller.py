import os
import json
from threading import Thread, Event
import time
import asyncio
from .motor_controller import motor_controller
from .focus_controller import focus_controller
from src.camera import CanonEOSR50
from src.settings import (
    MOTOR_IDS, PAN_TILT_VELOCITY, PAN_TILT_ACCELERATION,
    MOVEMENT_SETTINGS, DEFAULT_ACCELERATION, CAMERA_SETTINGS
)
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ProfileController:
    def __init__(self):
        self.playback_stop_event = Event()
        self.current_playback_thread = None
        self.tracking_active = False
        self.camera = None
        self.camera_connected = False
        self.recording_active = False

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

        logger.warning("Position verification timed out or stopped")
        return False

    def has_focus_points(self, profile):
        """Check if profile has any focus points"""
        return any(point.get('focus_point_id') is not None for point in profile['points'])

    async def connect_camera(self):
        """Connect to the camera."""
        try:
            # Clear any existing camera state
            if self.camera:
                try:
                    await self.camera.disconnect()
                except Exception as e:
                    logger.warning(f"Error disconnecting existing camera: {str(e)}")
                self.camera = None
                self.camera_connected = False
                self.recording_active = False

            # Create and connect new camera instance
            self.camera = CanonEOSR50()
            success = await self.camera.connect()
            
            if success:
                self.camera_connected = True
                logger.info("Camera connected and initialized successfully")
                return True, None
            else:
                self.camera = None
                logger.error("Failed to establish camera connection")
                return False, "Failed to connect to camera"
        except Exception as e:
            self.camera = None
            self.camera_connected = False
            logger.error(f"Error connecting to camera: {str(e)}", exc_info=True)
            return False, str(e)

    def run_profile(self, profile, settings):
        try:
            logger.info("Starting profile playback")
            
            # Connect camera if not already connected
            if not self.camera_connected:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success, error = loop.run_until_complete(self.connect_camera())
                if not success:
                    logger.error(f"Failed to connect camera: {error}")
            
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
                    
                    # Handle camera operations before movement
                    camera_action = point.get('camera_action', {})
                    if camera_action:
                        action_type = camera_action.get('type')
                        if action_type == 'photo':
                            # Wait for position if photo mode
                            if not self.verify_motor_positions(positions):
                                logger.warning(f"Motors didn't reach position for photo at point {i+1}")
                            time.sleep(CAMERA_SETTINGS['capture']['pre_delay'])
                            loop.run_until_complete(self.camera.capture_photo())
                            time.sleep(CAMERA_SETTINGS['capture']['post_delay'])
                        elif action_type == 'video_start' and not self.recording_active:
                            loop.run_until_complete(self.camera.start_video())
                            self.recording_active = True
                        elif action_type == 'video_stop' and self.recording_active:
                            loop.run_until_complete(self.camera.stop_video())
                            self.recording_active = False
                    
                    # Handle focus point changes
                    focus_point_id = point.get('focus_point_id')
                    if focus_point_id is not None:
                        focus_point = focus_controller.get_focus_point(focus_point_id)
                        if focus_point:
                            logger.debug(f"Starting/updating tracking for point {focus_point_id}")
                            success, error = focus_controller.start_tracking(focus_point)
                            if success:
                                logger.debug("Successfully activated tracking")
                                self.tracking_active = True
                            else:
                                logger.error(f"Failed to activate tracking: {error}")
                    
                    # Get and set point settings
                    duration = int(point.get('velocity', 1000))
                    positions = {
                        int(motor_id): int(pos) 
                        for motor_id, pos in point['positions'].items() 
                        if str(motor_id) not in [str(MOTOR_IDS['pan']), str(MOTOR_IDS['tilt'])]
                    }

                    # Set velocities
                    primary_velocity_dict = {
                        MOTOR_IDS['turntable']: duration,
                        MOTOR_IDS['slider']: duration,
                        MOTOR_IDS['zoom']: duration,
                        MOTOR_IDS['focus']: duration
                    }
                    
                    logger.debug(f"Setting velocities: primary={primary_velocity_dict}")
                    motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_profile_velocity, primary_velocity_dict)
                    
                    # Move motors
                    logger.debug(f"Moving to positions: {positions}")
                    if not motor_controller.safe_dxl_operation(motor_controller.dxl.bulk_write_goal_positions, positions):
                        raise Exception(f"Failed to move primary motors at point {i+1}")

                    # Wait for primary motors to reach their positions
                    if not self.verify_motor_positions(positions):
                        logger.warning(f"Primary motors didn't reach target positions at point {i+1}, continuing...")

                except Exception as e:
                    logger.error(f"Error processing point {i+1}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in profile playback: {str(e)}")
        finally:
            self.playback_stop_event.clear()
            # Stop video recording if still active
            if self.recording_active:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.camera.stop_video())
                self.recording_active = False
            # Don't stop tracking when playback ends - let user control it explicitly

    def start_playback(self, profile, settings):
        if self.current_playback_thread and self.current_playback_thread.is_alive():
            return False, "Playback already in progress"
            
        # Validate camera operations in profile
        if not self.camera_connected:
            for point in profile.get('points', []):
                if point.get('camera_action'):
                    return False, "Camera not connected. Cannot run profile with camera operations."
            
        try:
            self.playback_stop_event.clear()
            self.tracking_active = False
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
