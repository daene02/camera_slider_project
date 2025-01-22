from motor_control import MotorController
from settings import MOTOR_IDS

controller = MotorController()

try:
    # Teste Torque
    for motor_name, motor_id in MOTOR_IDS.items():
        print(f"Aktiviere Drehmoment für {motor_name}")
        controller.enable_torque(motor_id)

    # Setze Betriebsmodus
    print("Setze Betriebsmodus...")
    controller.set_operating_mode(MOTOR_IDS["slider"], 1)  # Velocity Control Mode
    controller.set_operating_mode(MOTOR_IDS["pan"], 3)    # Position Control Mode
    controller.set_operating_mode(MOTOR_IDS["tilt"], 3)   # Position Control Mode
    controller.set_operating_mode(MOTOR_IDS["turntable"], 1)  # Velocity Control Mode

    # Teste Geschwindigkeit
    print("Setze Geschwindigkeit für Slider...")
    controller.set_goal_velocity(MOTOR_IDS["slider"], 200)  # Testgeschwindigkeit
    print("Setze Geschwindigkeit für Turntable...")
    controller.set_goal_velocity(MOTOR_IDS["turntable"], 150)

    # Teste Position
    print("Setze Position für Pan...")
    controller.set_goal_position(MOTOR_IDS["pan"], 90, "pan")  # Testposition
    print("Setze Position für Tilt...")
    controller.set_goal_position(MOTOR_IDS["tilt"], -45, "tilt")  # Testposition

finally:
    # Torque deaktivieren
    for motor_name, motor_id in MOTOR_IDS.items():
        controller.disable_torque(motor_id)
    controller.close()
