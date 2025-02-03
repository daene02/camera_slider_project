from src.dxl_manager import DynamixelManager
from src.settings import (
    MOTOR_IDS, CONVERSION_FACTORS, MOTOR_OFFSETS,
    DEVICE_NAME, BAUD_RATE, PROTOCOL_VERSION,
    DEFAULT_VELOCITY, DEFAULT_ACCELERATION
)
import time

# Initialisiere den DynamixelManager
manager = DynamixelManager(
    device=DEVICE_NAME,
    baud=BAUD_RATE,
    protocol=PROTOCOL_VERSION,
    dxl_ids=list(MOTOR_IDS.values())
)

def apply_offsets(positions):
    adjusted_positions = {}
    for motor_name, position_values in positions.items():
        offset = MOTOR_OFFSETS.get(motor_name, 0)
        adjusted_positions[motor_name] = [pos - offset for pos in position_values]
    return adjusted_positions

def move_to_positions(manager, positions):
    positions_with_offsets = apply_offsets(positions)

    for step_index in range(len(next(iter(positions.values())))):
        target_positions = {}

        for motor_name, motor_id in MOTOR_IDS.items():
            position = positions_with_offsets[motor_name][step_index]
            conversion_factor = CONVERSION_FACTORS[motor_name]
            target_steps = int(position / conversion_factor)

            target_positions[motor_id] = target_steps

        print(f"Sende Zielpositionen: {target_positions}")
        manager.bulk_write_goal_positions(target_positions)
        manager.bulk_write_profile_velocity({motor_id: DEFAULT_VELOCITY for motor_id in MOTOR_IDS.values()})
        manager.bulk_write_profile_acceleration({motor_id: DEFAULT_ACCELERATION for motor_id in MOTOR_IDS.values()})

        wait_until_positions_reached(manager, target_positions)
        print("-- Punkt erreicht --")
        for motor_id, target in target_positions.items():
            current_position = manager.bulk_read_positions().get(motor_id, None)
            current_velocity = manager.bulk_read_profile_velocity().get(motor_id, None)
            current_acceleration = manager.bulk_read_profile_acceleration().get(motor_id, None)
            print(f"Motor ID {motor_id}: Soll = {target}, Ist = {current_position}, Velocity = {current_velocity}, Acceleration = {current_acceleration}")

def wait_until_positions_reached(manager, target_positions):
    while True:
        current_positions = manager.bulk_read_positions()
        all_reached = True

        for motor_id, target in target_positions.items():
            current = current_positions.get(motor_id, None)
            if current is None or abs(current - target) > 4:  # 10 Steps Toleranz
                all_reached = False
                break

        if all_reached:
            break

        time.sleep(0.01)  # Kurze Pause zwischen den Abfragen

try:
    print("Aktiviere Drehmoment für alle Motoren...")
    manager.enable_torque()

    start_positions = {
        "turntable": 0,
        "slider": 0,
        "pan": 0,
        "tilt": 0,
        "zoom": 0,
        "focus": 0
    }

    print("Bewege Motoren zu den Startpositionen...")
    move_to_positions(manager, {motor: [pos] for motor, pos in start_positions.items()})

    positions = {
        "turntable": [0, 90, 180, 270, 0],
        "slider": [200, 600, 800, 300, 0],
        "pan": [0, 160, -90, 20, 0],
        "tilt": [0, -56, 58, -56, 0],
        "zoom": [0, 50, 100, 50, 0],
        "focus": [0, 50, 75, 25, 0]
    }

    print("Synchronisiere Bewegungen...")
    move_to_positions(manager, positions)

finally:
    print("Deaktiviere Drehmoment und schließe Manager...")
    manager.disable_torque()
    manager.close()

print("Motor-Test abgeschlossen.")
