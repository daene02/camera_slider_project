"""Motor control and status management."""

import logging
from threading import Lock
from typing import Dict, List, Optional
from flask import jsonify
from src.dxl_manager import DynamixelManager
from src.enhanced_motor_control import EnhancedMotorControl
from src.camera_slider import CameraSlider
from src.settings import (
    CONVERSION_FACTORS, MOTOR_OFFSETS, MOTOR_IDS, MOTOR_NAMES, MOTION_CONTROL
)

logger = logging.getLogger(__name__)

class MotorController:
    def __init__(self):
        self.dxl = DynamixelManager()
        self.dxl_lock = Lock()
        self.enhanced = EnhancedMotorControl(self.dxl)
        self.slider = CameraSlider()

    def safe_dxl_operation(self, func, *args, **kwargs):
        with self.dxl_lock:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"DXL Operation error: {str(e)}")
                return None

    def get_motor_status(self):
        try:
            motors = []
            # Get filtered states from enhanced controller
            filtered_states = self.safe_dxl_operation(self.enhanced.get_filtered_positions) or {}
            
            # Get other motor data
            temperatures = self.safe_dxl_operation(self.dxl.bulk_read_temperature) or {}
            voltages = self.safe_dxl_operation(self.dxl.bulk_read_voltage) or {}
            currents = self.safe_dxl_operation(self.dxl.bulk_read_current) or {}
            velocities = self.safe_dxl_operation(self.dxl.bulk_read_profile_velocity) or {}
            accels = self.safe_dxl_operation(self.dxl.bulk_read_profile_acceleration) or {}
            torque_states = self.safe_dxl_operation(self.dxl.bulk_read_torque_enable) or {}
            pid_gains = self.safe_dxl_operation(self.dxl.bulk_read_pid_gains) or {}
            
            # Get current positions for all motors
            try:
                positions = self.safe_dxl_operation(self.dxl.bulk_read_positions) or {}
                converted_positions = {}
                for motor_name, motor_id in MOTOR_IDS.items():
                    if motor_id in positions:
                        steps = positions[motor_id]
                        conversion = CONVERSION_FACTORS[motor_name]
                        offset = MOTOR_OFFSETS.get(motor_name, 0)
                        converted_positions[motor_name] = steps * conversion - offset
                
                # Get Kalman filter predictions if available
                kalman_data = {}
                if hasattr(self.slider, 'motion_predictor') and converted_positions:
                    velocities_state = {name: 0.0 for name in converted_positions.keys()}
                    try:
                        pred_state = self.slider.motion_predictor.update(
                            measurements=converted_positions,
                            velocities=velocities_state
                        )
                        kalman_data = {
                            'slider': {
                                'prediction_time': pred_state.prediction_time * 1000,  # ms
                                'estimated_position': pred_state.slider_position,
                                'filter_uncertainty': float(self.slider.motion_predictor.filters['slider'].P[0, 0]),
                                'prediction_error': abs(converted_positions['slider'] - pred_state.slider_position)
                            },
                            'pan': {
                                'prediction_time': pred_state.prediction_time * 1000,
                                'estimated_position': pred_state.pan_angle,
                                'filter_uncertainty': float(self.slider.motion_predictor.filters['pan'].P[0, 0]),
                                'prediction_error': abs(converted_positions['pan'] - pred_state.pan_angle)
                            },
                            'tilt': {
                                'prediction_time': pred_state.prediction_time * 1000,
                                'estimated_position': pred_state.tilt_angle,
                                'filter_uncertainty': float(self.slider.motion_predictor.filters['tilt'].P[0, 0]),
                                'prediction_error': abs(converted_positions['tilt'] - pred_state.tilt_angle)
                            }
                        }
                    except Exception as e:
                        logger.error(f"Error getting Kalman predictions: {e}")
                        kalman_data = {}
            except Exception as e:
                logger.error(f"Error reading positions: {e}")
                converted_positions = {}
                kalman_data = {}
            
            # Build motor states list
            for motor_id in self.dxl.dxl_ids:
                motor_name = MOTOR_NAMES.get(motor_id, f"Motor {motor_id}")
                
                # Get filtered state values
                filtered_pos, filtered_vel, filtered_accel = filtered_states.get(motor_id, (0, 0, 0))
                
                # Get PID values for this motor
                pid = pid_gains.get(motor_id, {'p': 0, 'i': 0, 'd': 0})
                
                try:
                    # Build base motor state
                    motor_state = {
                        "id": motor_id,
                        "name": motor_name,
                        "position": filtered_pos,
                        "filtered_velocity": filtered_vel,
                        "filtered_acceleration": filtered_accel,
                        "temperature": temperatures.get(motor_id, 0),
                        "voltage": voltages.get(motor_id, 0) / 10.0,
                        "current": currents.get(motor_id, 0),
                        "speed": velocities.get(motor_id, 0),
                        "load": accels.get(motor_id, 0),
                        "torque_enabled": torque_states.get(motor_id, False),
                    "position_pid": {
                        "p": pid.get('p', 0),
                        "i": pid.get('i', 0),
                        "d": pid.get('d', 0)
                    },
                    "velocity_pid": {
                        "p": pid.get('vel_p', 0),
                        "i": pid.get('vel_i', 0)
                    }
                    }
                    
                    # Add Kalman filter data for supported motors
                    if motor_name in ['slider', 'pan', 'tilt'] and motor_name in kalman_data:
                        motor_state.update(kalman_data[motor_name])
                    
                    motors.append(motor_state)
                except Exception as e:
                    logger.error(f"Error building motor state for {motor_name}: {e}")
                    continue
            
            return motors
            
        except Exception as e:
            logger.error(f"Error in get_motor_status: {str(e)}")
            return None

    def toggle_torque(self, motor_id=None, enable=False):
        if motor_id is None:
            if enable:
                self.safe_dxl_operation(self.dxl.enable_torque)
            else:
                self.safe_dxl_operation(self.dxl.disable_torque)
        else:
            if enable:
                self.safe_dxl_operation(self.dxl.enable_torque, [motor_id])
            else:
                self.safe_dxl_operation(self.dxl.disable_torque, [motor_id])

    def update_motor_position(self, motor_id: int, position: int, use_prediction: bool = True):
        """Aktualisiert die Motorposition mit optionaler prädiktiver Kontrolle"""
        if use_prediction and hasattr(self.slider, 'motion_predictor'):
            # Convert position to focus point for prediction
            motor_name = MOTOR_NAMES.get(motor_id, '')
            if motor_name == 'slider':
                # Update slider position and recalculate pan/tilt
                self.slider.move_motors(
                    [{"turntable": 0, "slider": position, "pan": 0, "tilt": 0}],
                    focus_point={"x": 400, "y": position, "z": -300}
                )
            else:
                # Use enhanced control for non-slider motors
                self.safe_dxl_operation(
                    self.enhanced.move_to_position,
                    motor_id,
                    position,
                    use_prediction
                )
        else:
            self.safe_dxl_operation(
                self.enhanced.move_to_position,
                motor_id,
                position,
                False
            )

    def update_motor_velocity(self, motor_id, velocity):
        self.safe_dxl_operation(self.dxl.bulk_write_profile_velocity, {motor_id: velocity})

    def update_motor_acceleration(self, motor_id, acceleration):
        self.safe_dxl_operation(self.dxl.bulk_write_profile_acceleration, {motor_id: acceleration})

    def get_motor_positions(self):
        return self.safe_dxl_operation(self.dxl.bulk_read_positions)

    def steps_to_units(self, steps, motor):
        value = steps * CONVERSION_FACTORS[motor]
        if motor in MOTOR_OFFSETS:
            return value - MOTOR_OFFSETS[motor]
        return value

    def units_to_steps(self, units, motor):
        if motor in MOTOR_OFFSETS:
            units += MOTOR_OFFSETS[motor]
        return round(units / CONVERSION_FACTORS[motor])

    def update_pid_values(self, pid_dict):
        """
        Aktualisiert die PID-Werte für die angegebenen Motoren.
        pid_dict Format: {motor_id: {'p': value, 'i': value, 'd': value}}
        """
        return self.safe_dxl_operation(self.dxl.bulk_write_position_pid_gains, pid_dict)

    def move_motors_profile(self, positions, duration):
        """Führt eine profilierte Bewegung für mehrere Motoren aus"""
        self.safe_dxl_operation(
            self.enhanced.move_with_profile,
            positions,
            duration
        )

    def get_pid_values(self):
        """Liest die PID-Werte aller Motoren."""
        return self.safe_dxl_operation(self.dxl.bulk_read_pid_gains)

motor_controller = MotorController()
