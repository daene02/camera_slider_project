from threading import Lock
from flask import jsonify
from src.dxl_manager import DynamixelManager
from src.enhanced_motor_control import EnhancedMotorControl
from src.settings import (
    CONVERSION_FACTORS, MOTOR_OFFSETS, MOTOR_IDS, MOTOR_NAMES
)

class MotorController:
    def __init__(self):
        self.dxl = DynamixelManager()
        self.dxl_lock = Lock()
        self.enhanced = EnhancedMotorControl(self.dxl)

    def safe_dxl_operation(self, func, *args, **kwargs):
        with self.dxl_lock:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"DXL Operation error: {str(e)}")
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
            
            for motor_id in self.dxl.dxl_ids:
                # Get filtered state values
                filtered_pos, filtered_vel, filtered_accel = filtered_states.get(motor_id, (0, 0, 0))
                
                # Get PID values for this motor
                pid = pid_gains.get(motor_id, {})
                
                motors.append({
                    "id": motor_id,
                    "name": MOTOR_NAMES.get(motor_id, f"Motor {motor_id}"),
                    "position": filtered_pos,
                    "filtered_velocity": filtered_vel,
                    "filtered_acceleration": filtered_accel,
                    "temperature": temperatures.get(motor_id, 0),
                    "voltage": voltages.get(motor_id, 0) / 10.0,
                    "current": currents.get(motor_id, 0),
                    "speed": velocities.get(motor_id, 0),
                    "load": accels.get(motor_id, 0),
                    "torque_enabled": torque_states.get(motor_id, False),
                    "pid": {
                        "p": pid.get('p', 0),
                        "i": pid.get('i', 0),
                        "d": pid.get('d', 0)
                    }
                })
            return motors
        except Exception as e:
            print(f"Error in get_motor_status: {str(e)}")
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

    def update_motor_position(self, motor_id, position, use_prediction=True):
        """Aktualisiert die Motorposition mit optionaler prädiktiver Kontrolle"""
        self.safe_dxl_operation(
            self.enhanced.move_to_position,
            motor_id,
            position,
            use_prediction
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
        return self.safe_dxl_operation(self.dxl.bulk_write_pid_gains, pid_dict)

    def move_motors_profile(self, positions, duration):
        """Führt eine profilierte Bewegung für mehrere Motoren aus"""
        self.safe_dxl_operation(
            self.enhanced.move_with_profile,
            positions,
            duration
        )

    def get_pid_values(self):
        """Liest die PID-Werte aller Motoren."""
        return self.safe_dxl_operation(self.enhanced.get_pid_values)

motor_controller = MotorController()
