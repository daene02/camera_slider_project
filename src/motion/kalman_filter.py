"""
Kalman Filter implementation for motion prediction and smoothing.
"""

import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class KalmanState:
    position: float
    velocity: float
    acceleration: float

class KalmanFilter:
    def __init__(self, dt: float, q_settings: Dict[str, float], r: float, p0: float):
        """
        Initialize Kalman filter for 3-state tracking (position, velocity, acceleration)
        
        Args:
            dt: Time step
            q_settings: Process noise parameters for each state
            r: Measurement noise
            p0: Initial uncertainty
        """
        # State transition matrix
        self.F = np.array([
            [1, dt, 0.5*dt**2],
            [0,  1,        dt],
            [0,  0,         1]
        ])
        
        # Measurement matrix (we only measure position)
        self.H = np.array([[1, 0, 0]])
        
        # Process noise matrix
        self.Q = np.diag([
            q_settings['position'],
            q_settings['velocity'],
            q_settings['acceleration']
        ])
        
        # Measurement noise
        self.R = np.array([[r]])
        
        # Initial state
        self.x = np.zeros((3, 1))  # [position, velocity, acceleration]
        
        # Initial uncertainty
        self.P = np.eye(3) * p0
        
        self._initialized = False
        
    def update_time_step(self, dt: float):
        """Update time step for state transition"""
        self.F[0, 1] = dt
        self.F[0, 2] = 0.5 * dt**2
        self.F[1, 2] = dt
        
    def predict(self) -> KalmanState:
        """
        Predict next state
        
        Returns:
            KalmanState with predicted position, velocity, and acceleration
        """
        # State prediction
        self.x = self.F @ self.x
        
        # Covariance prediction
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        return KalmanState(
            position=float(self.x[0]),
            velocity=float(self.x[1]),
            acceleration=float(self.x[2])
        )
        
    def update(self, measurement: float, measured_velocity: float = None) -> KalmanState:
        """
        Update state with new measurements
        
        Args:
            measurement: New position measurement
            measured_velocity: Optional velocity measurement or profile velocity
            
        Returns:
            KalmanState with updated position, velocity, and acceleration
        """
        if not self._initialized:
            self.x[0] = measurement
            if measured_velocity is not None:
                self.x[1] = measured_velocity
            self._initialized = True
            return KalmanState(
                position=measurement,
                velocity=measured_velocity if measured_velocity is not None else 0.0,
                acceleration=0.0
            )
            
        # Adjust measurement model based on available measurements
        if measured_velocity is not None:
            # Extended measurement matrix and vector for position and velocity
            H = np.array([[1, 0, 0],
                         [0, 1, 0]])
            y = np.array([[measurement],
                         [measured_velocity]])
            R = np.array([[self.R[0,0], 0],
                         [0, self.R[0,0]*2]])  # Velocity measurement more uncertain
        else:
            # Just position measurement
            H = self.H
            y = np.array([[measurement]])
            R = self.R
            
        # Innovation calculation
        innovation = y - H @ self.x if measured_velocity is None else y - H @ self.x
        
        # Innovation covariance
        S = H @ self.P @ H.T + R
        
        # Kalman gain
        K = self.P @ H.T @ np.linalg.inv(S)
        
        # State update
        self.x = self.x + K @ innovation
        
        # Covariance update
        I = np.eye(3)
        self.P = (I - K @ H) @ self.P
        
        return KalmanState(
            position=float(self.x[0]),
            velocity=float(self.x[1]),
            acceleration=float(self.x[2])
        )
        
    def reset(self):
        """Reset filter state"""
        self.x = np.zeros((3, 1))
        self.P = np.eye(3) * self.P[0, 0]  # Keep initial uncertainty
        self._initialized = False
