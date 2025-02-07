import os
import json
from threading import Thread, Event
import time
from src.focus import FocusController as BaseFocusController
from .motor_controller import motor_controller
from src.settings import (
    MOTOR_IDS, UPDATE_INTERVAL, FOCUS_ENABLED
)
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class FocusController:
    def __init__(self):
        logger.info("=== Initializing FocusController ===")
        self.focus_points = []
        self.load_focus_points()
        self.active_controller = None
        self.active_point = None
        self.tracking_stop_event = Event()
        self.current_tracking_thread = None
        self.auto_focus = False

    def get_focus_points_path(self):
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(base_dir, 'profiles', 'focus_points.json')
        logger.debug(f"Focus points path: {path}")
        return path

    def load_focus_points(self):
        logger.info("=== Loading Focus Points ===")
        try:
            path = self.get_focus_points_path()
            logger.debug(f"Loading focus points from: {path}")
            
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = f.read()
                    logger.debug(f"Raw file content: {data}")
                    self.focus_points = json.loads(data)
                
                # Ensure all points have required fields
                self.focus_points = [
                    {
                        'id': p.get('id', i),
                        'name': p.get('name', f'Point {i + 1}'),
                        'description': p.get('description', ''),
                        'x': float(p.get('x', 0)),
                        'y': float(p.get('y', 0)),
                        'z': float(p.get('z', 0)),
                        'color': p.get('color', '#4a9eff'),
                        'created_at': p.get('created_at', datetime.now().isoformat()),
                        'updated_at': p.get('updated_at', datetime.now().isoformat())
                    }
                    for i, p in enumerate(self.focus_points)
                ]
                
                logger.info(f"Loaded {len(self.focus_points)} points: {self.focus_points}")
            else:
                logger.warning(f"Focus points file not found at {path}")
                self.focus_points = []
        except Exception as e:
            logger.error(f"Error loading focus points: {str(e)}")
            import traceback
            traceback.print_exc()
            self.focus_points = []

    def save_focus_points(self):
        logger.info("=== Saving Focus Points ===")
        try:
            path = self.get_focus_points_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            logger.debug(f"Saving focus points to {path}: {self.focus_points}")
            with open(path, 'w') as f:
                json.dump(self.focus_points, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving focus points: {str(e)}")
            return False

    def add_focus_point(self, point_data):
        """Add a new focus point with metadata"""
        logger.info(f"=== Adding Focus Point ===\n{point_data}")
        
        if not all(k in point_data for k in ('x', 'y', 'z')):
            logger.error("Missing required coordinates")
            return False, None

        try:
            point = {
                'id': len(self.focus_points),
                'name': point_data.get('name', f'Point {len(self.focus_points) + 1}'),
                'description': point_data.get('description', ''),
                'x': float(point_data['x']),
                'y': float(point_data['y']),
                'z': float(point_data['z']),
                'color': point_data.get('color', '#4a9eff'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.focus_points.append(point)
            logger.info(f"Added point: {point}")
            
            if self.save_focus_points():
                return True, point
            return False, "Failed to save points"
            
        except Exception as e:
            logger.error(f"Error adding point: {str(e)}")
            return False, str(e)

    def update_focus_point(self, point_id, point_data):
        """Update an existing focus point"""
        logger.info(f"=== Updating Focus Point ===\nID: {point_id}\nData: {point_data}")
        try:
            point_id = int(point_id)
            for i, point in enumerate(self.focus_points):
                if point['id'] == point_id:
                    # Update only provided fields
                    for key in ['name', 'description', 'x', 'y', 'z', 'color']:
                        if key in point_data:
                            point[key] = point_data[key]
                    point['updated_at'] = datetime.now().isoformat()
                    
                    # Update active point if this is the current point
                    if self.active_point and self.active_point['id'] == point_id:
                        self.set_focus_point(point)
                    
                    if self.save_focus_points():
                        logger.info(f"Updated point {point_id}: {point}")
                        return True, point
                    return False, "Failed to save points"
            
            logger.warning(f"Point not found: {point_id}")
            return False, "Point not found"
            
        except Exception as e:
            logger.error(f"Error updating point: {str(e)}")
            return False, str(e)

    def remove_focus_point(self, point_id):
        """Remove a focus point by its ID"""
        logger.info(f"=== Removing Focus Point ===\nID: {point_id}")
        try:
            point_id = int(point_id)
        except (TypeError, ValueError):
            logger.error(f"Invalid point ID format: {point_id}")
            return False, "Invalid point ID format"

        try:
            # Find and remove point
            point_index = None
            for i, p in enumerate(self.focus_points):
                if p['id'] == point_id:
                    point_index = i
                    break

            if point_index is None:
                logger.warning(f"Point not found: {point_id}")
                return False, "Point not found"

            # Clear active point if this is it
            if self.active_point and self.active_point['id'] == point_id:
                self.stop_tracking()

            # Remove point
            self.focus_points.pop(point_index)
            
            # Reindex remaining points
            for i, point in enumerate(self.focus_points):
                point['id'] = i

            # Save changes
            if self.save_focus_points():
                logger.info(f"Removed point {point_id}")
                return True, None
            return False, "Failed to save points after deletion"
            
        except Exception as e:
            error_msg = f"Error removing point: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_focus_point(self, point_id):
        """Get a focus point by its ID"""
        logger.debug(f"Getting point {point_id}")
        try:
            point_id = int(point_id)
            for point in self.focus_points:
                if point['id'] == point_id:
                    return point
            return None
        except Exception as e:
            logger.error(f"Error getting point: {str(e)}")
            return None

    def set_focus_point(self, point):
        """Set or update the current focus point"""
        if not FOCUS_ENABLED:
            logger.warning("Focus tracking is disabled in settings")
            return False, "Focus tracking is disabled"

        if not point:
            logger.warning("No point provided")
            return False, "No point provided"

        try:
            logger.info(f"Setting focus point: {point}")
            self.active_point = point
            
            # Create or update base focus controller
            if self.active_controller is None:
                logger.debug("Creating new base focus controller")
                self.active_controller = BaseFocusController(
                    object_position=(point['x'], point['y'], point['z'])
                )
            else:
                logger.debug("Updating base focus controller coordinates")
                self.active_controller.object_x = point['x']
                self.active_controller.object_y = point['y']
                self.active_controller.object_z = point['z']
                
            return True, None
        except Exception as e:
            error_msg = f"Error setting focus point: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def set_manual_focus(self, focus_value):
        """Set manual focus position"""
        try:
            focus_value = float(focus_value)
            if self.active_controller:
                clamped_value = self.active_controller.set_focus_position(focus_value)
                target_steps = motor_controller.units_to_steps(clamped_value, 'focus')
                motor_controller.safe_dxl_operation(
                    motor_controller.dxl.write_goal_position,
                    MOTOR_IDS['focus'],
                    target_steps
                )
                return True, clamped_value
            return False, "No active controller"
        except Exception as e:
            logger.error(f"Error setting manual focus: {str(e)}")
            return False, str(e)

    def track_focus_point(self, auto_focus=True):
        """Continuous focus tracking thread function"""
        if not FOCUS_ENABLED:
            logger.warning("Focus tracking is disabled in settings")
            return

        try:
            motor_controller.toggle_torque(enable=True)
            last_update_time = 0
            
            while not self.tracking_stop_event.is_set() and self.active_controller:
                current_time = time.time()
                
                # Throttle updates
                if current_time - last_update_time < UPDATE_INTERVAL:
                    time.sleep(0.001)
                    continue
                
                positions = motor_controller.get_motor_positions()
                if not positions or MOTOR_IDS['slider'] not in positions:
                    time.sleep(0.01)
                    continue

                try:
                    # Convert slider position to units
                    slider_pos = motor_controller.steps_to_units(positions[MOTOR_IDS['slider']], 'slider')
                    
                    # Calculate new positions
                    motor_positions = self.active_controller.get_motor_positions(slider_pos, include_focus=auto_focus)
                    
                    # Convert to steps
                    target_positions = {
                        MOTOR_IDS['pan']: motor_controller.units_to_steps(motor_positions['pan'], 'pan'),
                        MOTOR_IDS['tilt']: motor_controller.units_to_steps(motor_positions['tilt'], 'tilt'),
                    }
                    
                    # Include focus only if auto-focus is enabled
                    if auto_focus and 'focus' in motor_positions:
                        target_positions[MOTOR_IDS['focus']] = motor_controller.units_to_steps(motor_positions['focus'], 'focus')
                    
                    # Move motors
                    motor_controller.safe_dxl_operation(
                        motor_controller.dxl.bulk_write_goal_positions,
                        target_positions
                    )
                    
                    last_update_time = current_time
                    
                except Exception as e:
                    logger.error(f"Error during position calculation: {str(e)}")
                    time.sleep(0.1)
                    continue
                
        except Exception as e:
            logger.error(f"Error during focus tracking: {str(e)}")
        finally:
            self.tracking_stop_event.clear()

    def start_tracking(self, point, auto_focus=False):
        """
        Start focus tracking with given point
        Args:
            point: Focus point data
            auto_focus: Whether to enable automatic focus control
        """
        if not FOCUS_ENABLED:
            return False, "Focus tracking is disabled in settings"

        if self.current_tracking_thread and self.current_tracking_thread.is_alive():
            # If already tracking, just update the point
            success, error = self.set_focus_point(point)
            if success:
                self.auto_focus = auto_focus
            return success, error

        try:
            # Set up new tracking
            success, error = self.set_focus_point(point)
            if not success:
                return False, error

            # Set focus mode
            self.auto_focus = auto_focus

            # Start tracking thread
            self.tracking_stop_event.clear()
            self.current_tracking_thread = Thread(
                target=self.track_focus_point,
                args=(auto_focus,)
            )
            self.current_tracking_thread.start()
            return True, None

        except Exception as e:
            return False, str(e)

    def stop_tracking(self):
        """Stop focus tracking"""
        logger.info("Stopping focus tracking")
        self.tracking_stop_event.set()
        if self.current_tracking_thread:
            self.current_tracking_thread.join(timeout=1.0)
        self.active_point = None
        self.active_controller = None
        self.current_tracking_thread = None
        self.auto_focus = False
        motor_controller.toggle_torque(enable=False)
        return True

focus_controller = FocusController()
