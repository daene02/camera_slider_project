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
            # Velocity-based timing
            velocity_scale = abs(velocity) * pred_settings['smoothing']['velocity_scale']
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
        
        # Tilt angle (vertical rotation) - arctangent of z/horizontal displacement
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
        # Update time step based on slider velocity
        pred_time = self._calculate_prediction_time(
            velocities['slider'],
            profile_duration
        )
        
        for name, filter in self.filters.items():
            filter.update_time_step(pred_time)
            filter.update(measurements[name])
            
        # Predict next states
        slider_state = self.filters['slider'].predict()
        
        if self.focus_mode_active and self.current_focus_point:
            # Calculate required angles for predicted slider position
            pan_target, tilt_target = self._calculate_focus_angles(
                slider_state.position
            )
            
            # Update pan/tilt predictions with new targets
            self.filters['pan'].update(pan_target)
            self.filters['tilt'].update(tilt_target)
            
            # Get final predictions
            pan_state = self.filters['pan'].predict()
            tilt_state = self.filters['tilt'].predict()
        else:
            # When focus mode is off, maintain current positions
            pan_state = KalmanState(
                position=measurements['pan'],
                velocity=0.0,
                acceleration=0.0
            )
            tilt_state = KalmanState(
                position=measurements['tilt'],
                velocity=0.0,
                acceleration=0.0
            )
            
        return PredictedState(
            slider_position=slider_state.position,
            pan_angle=pan_state.position,
            tilt_angle=tilt_state.position,
            prediction_time=pred_time
        )
