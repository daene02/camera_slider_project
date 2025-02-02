from threading import Lock
from flask import jsonify
from src.dxl_manager import DynamixelManager

# Constants
CONVERSION_FACTORS = {
    "slider": 64 / 4096,     # 1 rotation = 64mm
    "pan": 360 / 4096,       # 1 rotation = 360 degrees
    "tilt": 360 / 4096,      # 1 rotation = 360 degrees
    "focus": 360 / 4096,     # 1 rotation = 360 degrees
    "turntable": 360 / 4096, # 1 rotation = 360 degrees
    "zoom": 360 / 4096       # 1 rotation = 360 degrees
}

MOTOR_OFFSETS = {
    "pan": 180,
    "tilt": 180
}

MOTOR_IDS = {
    "turntable": 1,
    "slider": 2,
    "pan": 3,
    "tilt": 4,
    "zoom": 5,
    "focus": 6
}

MOTOR_NAMES = {
    1: "Turntable",
    2: "Slider",
    3: "Pan",
    4: "Tilt",
    5: "Zoom",
    6: "Focus"
}

class MotorController:
    def __init__(self):
        self.dxl = DynamixelManager()
        self.dxl_lock = Lock()

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
            positions = self.safe_dxl_operation(self.dxl.bulk_read_positions) or {}
            temperatures = self.safe_dxl_operation(self.dxl.bulk_read_temperature) or {}
            voltages = self.safe_dxl_operation(self.dxl.bulk_read_voltage) or {}
            currents = self.safe_dxl_operation(self.dxl.bulk_read_current) or {}
            velocities = self.safe_dxl_operation(self.dxl.bulk_read_profile_velocity) or {}
            accels = self.safe_dxl_operation(self.dxl.bulk_read_profile_acceleration) or {}
            torque_states = self.safe_dxl_operation(self.dxl.bulk_read_torque_enable) or {}
            
            for motor_id in self.dxl.dxl_ids:
                motors.append({
                    "id": motor_id,
                    "name": MOTOR_NAMES.get(motor_id, f"Motor {motor_id}"),
                    "position": positions.get(motor_id, 0),
                    "temperature": temperatures.get(motor_id, 0),
                    "voltage": voltages.get(motor_id, 0) / 10.0,
                    "current": currents.get(motor_id, 0),
                    "speed": velocities.get(motor_id, 0),
                    "load": accels.get(motor_id, 0),
                    "torque_enabled": torque_states.get(motor_id, False)
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

    def update_motor_position(self, motor_id, position):
        self.safe_dxl_operation(self.dxl.bulk_write_goal_positions, {motor_id: position})

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

motor_controller = MotorController()
