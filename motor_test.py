from motor_control import MotorController
from settings import MOTOR_IDS, PID_DEFAULTS
from homing import HomingController
import time

controller = MotorController()
#homing_controller = HomingController(controller.port_handler, controller.packet_handler)

def read_pid_values(controller, motor_id):
    velocity_i_gain = controller.packet_handler.read2ByteTxRx(controller.port_handler, motor_id, 76)[0]
    velocity_p_gain = controller.packet_handler.read2ByteTxRx(controller.port_handler, motor_id, 78)[0]
    position_d_gain = controller.packet_handler.read2ByteTxRx(controller.port_handler, motor_id, 80)[0]
    position_i_gain = controller.packet_handler.read2ByteTxRx(controller.port_handler, motor_id, 82)[0]
    position_p_gain = controller.packet_handler.read2ByteTxRx(controller.port_handler, motor_id, 84)[0]

    return {
        "velocity_i_gain": velocity_i_gain,
        "velocity_p_gain": velocity_p_gain,
        "position_d_gain": position_d_gain,
        "position_i_gain": position_i_gain,
        "position_p_gain": position_p_gain
    }

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

    print("Lese PID-Werte für die Motoren...")
    for motor_name, motor_id in MOTOR_IDS.items():
        pid_values = read_pid_values(controller, motor_id)
        print(f"Motor: {motor_name} (ID: {motor_id})")
        for key, value in pid_values.items():
            print(f"  {key}: {value}")

    print("Setze Betriebsmodi für die Motoren...")
    controller.set_operating_mode(MOTOR_IDS["slider"], 4)  # Position Control Mode
    controller.set_operating_mode(MOTOR_IDS["pan"], 3)  # Position Control Mode
    controller.set_operating_mode(MOTOR_IDS["tilt"], 3)  # Position Control Mode

    print("Aktiviere Drehmoment für alle Motoren...")
    for motor_name, motor_id in MOTOR_IDS.items():
        controller.enable_torque(motor_id)

    print("Setze Profile für die Motoren...")

    def calculate_wait_time(velocity):
        base_wait_time = -1
        velocity_factor = velocity / 1000.0
        wait_time = base_wait_time + velocity_factor
        print(f"Berechnete Wartezeit: {wait_time:.2f} Sekunden für Geschwindigkeit {velocity}")
        return wait_time

    positions = [
        {"turntable": 0, "slider": 0, "pan": 112, "tilt": 69, "shared_velocity": 8000},
        {"turntable": 0, "slider": 0, "pan": 112, "tilt": 69, "shared_velocity": 8000},
        {"turntable": 0, "slider": 300, "pan": 134, "tilt": 86, "shared_velocity": 30000},
        {"turntable": 0, "slider": 560, "pan": 178, "tilt": 101, "shared_velocity": 30000},
        {"turntable": 0, "slider": 560, "pan": 178, "tilt": 101, "shared_velocity": 3000},
        {"turntable": -90, "slider": 560, "pan": 178, "tilt": 101, "shared_velocity": 6000},
        {"turntable": -90, "slider": 560, "pan": 178, "tilt": 101, "shared_velocity": 3000},
        {"turntable": -180, "slider": 560, "pan": 178, "tilt": 101, "shared_velocity": 6000},
        {"turntable": -180, "slider": 560, "pan": 178, "tilt": 101, "shared_velocity": 3000},
        {"turntable": -270, "slider": 560, "pan": 178, "tilt": 101, "shared_velocity": 6000},
        {"turntable": -270, "slider": 560, "pan": 178, "tilt": 101, "shared_velocity": 3000},
        {"turntable": -360, "slider": 560, "pan": 178, "tilt": 101, "shared_velocity": 6000},
        {"turntable": -180, "slider": 300, "pan": 131, "tilt": 83, "shared_velocity": 30000},
        {"turntable": 0, "slider": 0, "pan": 112, "tilt": 69, "shared_velocity": 30000},
        {"turntable": 0, "slider": 0, "pan": 112, "tilt": 69, "shared_velocity": 8000},
        {"turntable": 0, "slider": 0, "pan": 90, "tilt": 102, "shared_velocity": 8000},
    ]

    for i, position in enumerate(positions):
        print(f"Fahre Position {i + 1} an: {position}")

        shared_velocity = position["shared_velocity"]
        pan_velocity_offset = -1000  # Beispiel für Offset für Pan
        tilt_velocity_offset = -1000  # Beispiel für Offset für Tilt

        controller.set_profile(MOTOR_IDS["turntable"], shared_velocity, 3000)
        controller.set_profile(MOTOR_IDS["slider"], shared_velocity, 32000)
        controller.set_profile(MOTOR_IDS["pan"], max(shared_velocity + pan_velocity_offset, 0), 32000)
        controller.set_profile(MOTOR_IDS["tilt"], max(shared_velocity + tilt_velocity_offset, 0), 32000)

        status = controller.bulk_read_status(MOTOR_IDS.values())
        print(f"Motorstatus: {status}")

        controller.set_goal_position(MOTOR_IDS["turntable"], position["turntable"])
        controller.set_goal_position(MOTOR_IDS["slider"], position["slider"])
        controller.set_goal_position(MOTOR_IDS["pan"], position["pan"])
        controller.set_goal_position(MOTOR_IDS["tilt"], position["tilt"])

        wait_time = position.get("wait_time", calculate_wait_time(shared_velocity))
        print(f"Wartezeit wird gestartet: {wait_time:.2f} Sekunden")
        time.sleep(wait_time)

finally:
    print("Deaktiviere Drehmoment und schließe Controller...")
    for motor_id in MOTOR_IDS.values():
        controller.disable_torque(motor_id)
    controller.close()

print("Motor-Test abgeschlossen.")
