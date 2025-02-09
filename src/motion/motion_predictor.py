"""
Motion prediction and focus point tracking system.
Uses Kalman filtering for smooth position prediction.
"""

import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from .kalman_filter import KalmanFilter, KalmanState
from src.settings import MOTION_CONTROL

@dataclass
class PredictedState:
    slider_position: float
    pan_angle: float
    tilt_angle: float
    prediction_time: float

class MotionPredictor:
    def __init__(self):
        """Initialize motion prediction system with Kalman filters"""
        self.kalman_settings = MOTION_CONTROL['slave_kalman']
        self.prediction_settings = MOTION_CONTROL['prediction']
        
        # Initialize Kalman filters for each axis
        self._init_kalman_filters()
        
        self.focus_mode_active = False
        self.current_focus_point = None
        
        # Velocity limits
        self.velocity_limits = {
            'slider': 500.0,  # mm/s
            'pan': 180.0,    # deg/s
            'tilt': 180.0    # deg/s
        }
        
    def _normalize_angle(self, angle: float) -> float:
        """Normalize angle to -180 to +180 range"""
        angle = angle % 360
        if angle > 180:
            angle -= 360
        return angle
        
    def _limit_velocity(self, velocity: float, motor_name: str) -> float:
        """Apply velocity limits based on motor type"""
        limit = self.velocity_limits.get(motor_name, 180.0)
        return np.clip(velocity, -limit, limit)
        
    def _init_kalman_filters(self):
        """Initialize separate Kalman filters for each axis"""
        default_dt = self.kalman_settings['update_rate']
        q_settings = self.kalman_settings['process_noise']
        r = self.kalman_settings['measurement_noise']
        p0 = self.kalman_settings['initial_uncertainty']
        
        self.filters = {
            'slider': KalmanFilter(default_dt, q_settings, r, p0),
            'pan': KalmanFilter(default_dt, q_settings, r, p0),
            'tilt': KalmanFilter(default_dt, q_settings, r, p0)
        }
        
    def _calculate_prediction_time(self, velocity: float, profile_duration: Optional[float] = None) -> float:
        """
        Calculate adaptive prediction time based on velocity and profile
        
        Args:
            velocity: Current velocity in units/s
            profile_duration: Optional duration from time-based profile
            
        Returns:
            Prediction time in seconds
        """
        pred_settings = self.prediction_settings
        
        # Use profile-based timing if available
        if profile_duration is not None:
            base_time = profile_duration * 0.01  # 1% of profile duration
        else:
            # Velocity-based timing with normalized velocity
            norm_velocity = abs(velocity) / self.velocity_limits['slider']
            velocity_scale = norm_velocity * pred_settings['smoothing']['velocity_scale']
            base_time = pred_settings['time'] * (1.0 + velocity_scale)
            
        # Apply min/max limits
        return np.clip(base_time, 
                      pred_settings['min_time'],
                      pred_settings['max_time'])
                      
    def _calculate_focus_angles(self, slider_position: float) -> Tuple[float, float]:
        """
        Calculate required pan/tilt angles to keep focus on target point.
        Uses camera position relative to focus point to calculate angles.
        
        Args:
            slider_position: Current slider position in mm
            
        Returns:
            Tuple of (pan_angle, tilt_angle) in degrees
        """
        if not self.current_focus_point:
            return 0.0, 0.0
        
        # Get camera position from slider position and turntable position
        from src.settings import TURNTABLE_POSITION
        camera_x = TURNTABLE_POSITION["x"]  # Static X offset
        camera_y = slider_position          # Y position from slider
        camera_z = TURNTABLE_POSITION["z"]  # Static Z height
        
        # Calculate vectors to focus point
        dx = self.current_focus_point["x"] - camera_x
        dy = self.current_focus_point["y"] - camera_y
        dz = self.current_focus_point["z"] - camera_z
        
        # Calculate angles
        # Pan angle (horizontal rotation) - arctangent of x/y displacement
        pan_angle = np.degrees(np.arctan2(dx, dy))
        
        # Tilt angle (vertical rotation) - arctangent of z/horizontal distance
        horizontal_distance = np.sqrt(dx*dx + dy*dy)
        tilt_angle = np.degrees(np.arctan2(dz, horizontal_distance))
        
        return pan_angle, tilt_angle
        
    def set_focus_point(self, point: Dict[str, float]):
        """
        Set new focus point for tracking
        
        Args:
            point: Dictionary with x,y,z coordinates of focus point
        """
        self.current_focus_point = point
        
    def enable_focus_mode(self, enable: bool):
        """Enable or disable focus tracking mode"""
        self.focus_mode_active = enable
        if not enable:
            # Reset Kalman filters when disabling focus mode
            for filter in self.filters.values():
                filter.reset()
                
    def update(self, 
              measurements: Dict[str, float], 
              velocities: Dict[str, float],
              profile_duration: Optional[float] = None) -> PredictedState:
        """
        Update state with new measurements and predict next positions
        
        Args:
            measurements: Current positions for slider, pan, tilt
            velocities: Current velocities for slider, pan, tilt
            profile_duration: Optional duration from time-based profile
            
        Returns:
            PredictedState with predicted positions
        """
        # Update time step based on profile or velocity
        if profile_duration is not None:
            pred_time = min(
                profile_duration * 0.1,  # 10% of profile duration
                self.prediction_settings['max_time']
            )
            pred_time = max(pred_time, self.prediction_settings['min_time'])
        else:
            pred_time = self._calculate_prediction_time(
                velocities['slider'],
                None
            )
        
        # Apply velocity limits and calculate time-based velocities
        limited_velocities = {}
        for name in self.filters.keys():
            current_pos = measurements[name]
            target_velocity = velocities.get(name, 0.0)
            
            if profile_duration is not None and profile_duration > 0:
                # Calculate velocity from position difference and duration
                start_pos = measurements[name]
                target_pos = target_velocity  # In this case, target_velocity contains target position
                distance = target_pos - start_pos
                # Calculate velocity to reach target in given duration
                velocity = distance / profile_duration
            else:
                # Use direct velocity with limits
                velocity = self._limit_velocity(target_velocity, name)
            
            # Store calculated velocity
            limited_velocities[name] = velocity
        
        # Update filters with time step and measurements
        for name, filter in self.filters.items():
            # Update time step for prediction
            filter.update_time_step(pred_time)
            
            # Get current velocity from profile or direct measurement
            current_velocity = limited_velocities[name]
            
            # Update filter with both position and velocity
            filter.update(
                measurement=measurements[name],
                measured_velocity=current_velocity
            )
            
            # Force immediate update if we have profile duration
            if profile_duration is not None:
                filter.predict()  # Additional prediction step for smoother updates
            
        # Predict next states
        slider_state = self.filters['slider'].predict()
        
        if self.focus_mode_active and self.current_focus_point:
            # Calculate required angles for predicted slider position
            pan_target, tilt_target = self._calculate_focus_angles(
                slider_state.position
            )
            
            # Update pan/tilt predictions with new targets
            self.filters['pan'].update(pan_target, measured_velocity=limited_velocities['pan'])
            self.filters['tilt'].update(tilt_target, measured_velocity=limited_velocities['tilt'])
            
            # Get final predictions and normalize angles
            pan_state = self.filters['pan'].predict()
            tilt_state = self.filters['tilt'].predict()
            
            # Normalize angles and limit velocities
            pan_state = KalmanState(
                position=self._normalize_angle(pan_state.position),
                velocity=self._limit_velocity(pan_state.velocity, 'pan'),
                acceleration=pan_state.acceleration
            )
            
            tilt_state = KalmanState(
                position=self._normalize_angle(tilt_state.position),
                velocity=self._limit_velocity(tilt_state.velocity, 'tilt'),
                acceleration=tilt_state.acceleration
            )
        else:
            # When focus mode is off, use current error for correction
            pan_error = measurements['pan'] - self.filters['pan'].x[0, 0]
            tilt_error = measurements['tilt'] - self.filters['tilt'].x[0, 0]
            
            # Update pan filter with error correction
            self.filters['pan'].update(
                measurements['pan'],
                measured_velocity=velocities.get('pan', 0.0)
            )
            pan_state = self.filters['pan'].predict()
            
            # Update tilt filter with error correction
            self.filters['tilt'].update(
                measurements['tilt'],
                measured_velocity=velocities.get('tilt', 0.0)
            )
            tilt_state = self.filters['tilt'].predict()
            
            # Apply corrections and normalize
            pan_state = KalmanState(
                position=self._normalize_angle(pan_state.position + pan_error * 0.5),
                velocity=self._limit_velocity(pan_state.velocity, 'pan'),
                acceleration=pan_state.acceleration
            )
            
            tilt_state = KalmanState(
                position=self._normalize_angle(tilt_state.position + tilt_error * 0.5),
                velocity=self._limit_velocity(tilt_state.velocity, 'tilt'),
                acceleration=tilt_state.acceleration
            )
            
        return PredictedState(
            slider_position=slider_state.position,
            pan_angle=pan_state.position,
            tilt_angle=tilt_state.position,
            prediction_time=pred_time
        )
