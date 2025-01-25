from motor_control import MotorController
from settings import MOTOR_IDS, PID_DEFAULTS, CONVERSION_FACTORS, VELOCITY_LIMIT_ADDRESS
import time
import numpy as np
from scipy.interpolate import CubicSpline
import asyncio

controller = MotorController()

VELOCITY_LIMITS = {
    "turntable": 1800,
    "slider": 2500,
    "pan": 1800,
    "tilt":1800
}

def smooth_trajectory(positions, resolution=1000):
    x = np.linspace(0, len(positions["slider"]) - 1, len(positions["slider"]))
    smoothed = {}

    for axis, values in positions.items():
        spline = CubicSpline(x, values)
        smoothed[axis] = spline(np.linspace(0, len(positions["slider"]) - 1, resolution))

    return smoothed

def validate_target_steps(motor_name, target_steps):
    conversion_factor = CONVERSION_FACTORS[motor_name]
    min_limit = int(PID_DEFAULTS[motor_name].get("min_limit", 0) / conversion_factor)
    max_limit = int(PID_DEFAULTS[motor_name].get("max_limit", 4096) / conversion_factor)
    if not (min_limit <= target_steps <= max_limit):
        print(f"Zielposition {target_steps} für Motor {motor_name} liegt außerhalb der Grenzen ({min_limit}, {max_limit}).")
        return False
    return True

def correct_motor_position(controller, motor_id, target_position, tolerance=0.5):
    motor_name = next(name for name, id in MOTOR_IDS.items() if id == motor_id)
    conversion_factor = CONVERSION_FACTORS[motor_name]
    actual_steps = controller.get_present_position(motor_id)
    actual_position = actual_steps * conversion_factor

    if abs(actual_position - target_position) > tolerance:
        target_steps = int(target_position / conversion_factor)
        if not validate_target_steps(motor_name, target_steps):
            return

        print(f"Korrigiere Position: Motor ID={motor_id}, Soll={target_position}, Ist={actual_position}, Ziel in Schritten={target_steps}")
        controller.set_goal_position(motor_id, target_steps)

def move_to_start(controller, start_positions):
    for motor_name, motor_id in MOTOR_IDS.items():
        start_position = start_positions[motor_name]
        conversion_factor = CONVERSION_FACTORS.get(motor_name, 1)
        target_steps = int(start_position / conversion_factor)

        if not validate_target_steps(motor_name, target_steps):
            continue

        print(f"Bewege Motor {motor_name} (ID={motor_id}) zur Startposition: {start_position}")
        controller.set_goal_position(motor_id, target_steps)
        time.sleep(1)

def synchronize_movements(controller, positions, resolution=3000, duration=10):
    smoothed_positions = smooth_trajectory(positions, resolution)
    step_duration = duration / resolution

    for i in range(resolution):
        turntable = smoothed_positions["turntable"][i]
        slider = smoothed_positions["slider"][i]
        pan = smoothed_positions["pan"][i]
        tilt = smoothed_positions["tilt"][i]

        for motor_name, position in zip(["turntable", "slider", "pan", "tilt"], [turntable, slider, pan, tilt]):
            motor_id = MOTOR_IDS[motor_name]
            conversion_factor = CONVERSION_FACTORS[motor_name]
            target_steps = int(position / conversion_factor)

            if not validate_target_steps(motor_name, target_steps):
                continue

            velocity = abs(position - controller.get_present_position(motor_id)) / step_duration
            velocity_steps = min(int(velocity / conversion_factor), VELOCITY_LIMITS[motor_name])

            print(f"Motor: {motor_name}, Ziel: {position}, Geschwindigkeit: {velocity_steps}")
            controller.set_profile(motor_id, velocity_steps, acceleration=5000)
            controller.set_goal_position(motor_id, target_steps)

        for motor_name, motor_id in MOTOR_IDS.items():
            current_position = controller.get_present_position(motor_id)
            target_position = smoothed_positions[motor_name][i]
            correct_motor_position(controller, motor_id, target_position)

        time.sleep(step_duration)

try:
    print("Setze PID-Werte für die Motoren...")
    for motor_name, motor_id in MOTOR_IDS.items():
        pid_values = PID_DEFAULTS[motor_name]
        controller.set_pid_gains(
            motor_id,
            pid_values["velocity_i_gain"],
            pid_values["velocity_p_gain"],
            pid_values["position_d_gain"],
            pid_values["position_i_gain"],
            pid_values["position_p_gain"]
        )

    print("Setze Betriebsmodi für die Motoren...")
    controller.set_operating_mode(MOTOR_IDS["slider"], 4)
    controller.set_operating_mode(MOTOR_IDS["pan"], 3)
    controller.set_operating_mode(MOTOR_IDS["tilt"], 3)
    controller.set_operating_mode(MOTOR_IDS["turntable"], 3)

    print("Aktiviere Drehmoment für alle Motoren...")
    for motor_name, motor_id in MOTOR_IDS.items():
        controller.enable_torque(motor_id)

    print("Fahre zu den Startpositionen...")
    start_positions = {
        "turntable": 0,
        "slider": 0,
        "pan": 10,
        "tilt": 20
    }
    move_to_start(controller, start_positions)

    positions = {
        "turntable": [0, 90, 180, 270, 0],
        "slider": [0, 100, 600, 300, 0],
        "pan": [10, 180, 100, 20, 0],
        "tilt": [20, 30, 90, 60, 0]
    }

    durations = [5]

    print("Synchronisiere Bewegungen...")
    for duration in durations:
        synchronize_movements(controller, positions, resolution=400, duration=duration)

finally:
    print("Deaktiviere Drehmoment und schließe Controller...")
    for motor_id in MOTOR_IDS.values():
        controller.disable_torque(motor_id)
    controller.close()

print("Motor-Test abgeschlossen.")
