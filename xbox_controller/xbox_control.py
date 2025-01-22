import threading
from inputs import get_gamepad
import time
from motor_control import MotorController
from settings import MOTOR_IDS, MOTOR_LIMITS

class XboxController:
    def __init__(self, controller):
        self.controller = controller
        self.running = True

        # Statusvariablen
        self.rpm = 100
        self.torque_enabled = {motor: False for motor in MOTOR_IDS}
        self.max_velocity = 300  # Geschwindigkeit für Slider, Pan und Tilt erhöht
        self.centering = False  # Für das langsame Zurücksetzen zur Mitte

    def start_controller_thread(self):
        """Startet den Thread für den Xbox-Controller."""
        thread = threading.Thread(target=self.listen_controller)
        thread.daemon = True
        thread.start()

    def listen_controller(self):
        """Liests den Xbox-Controller aus und führt Aktionen aus."""
        try:
            while self.running:
                events = get_gamepad()
                for event in events:
                    self.process_event(event)
                time.sleep(0.01)
        except Exception as e:
            print(f"Controller Fehler: {e}")

    def process_event(self, event):
        """Verarbeitet Controller-Eingaben."""
        print(f"Event: {event.ev_type}, Code: {event.code}, State: {event.state}")  # Debugging-Ausgabe
        if event.ev_type == "Key" and event.code == "BTN_SOUTH":  # 'A'-Taste
            self.toggle_torque_slider_pan_tilt(True)
        elif event.ev_type == "Key" and event.code == "BTN_WEST":  # 'X'-Taste
            self.toggle_torque_slider_pan_tilt(False)
        elif event.ev_type == "Key" and event.code == "BTN_EAST":  # 'B'-Taste
            self.toggle_torque_turntable(True)
        elif event.ev_type == "Key" and event.code == "BTN_NORTH":  # 'Y'-Taste
            self.toggle_torque_turntable(False)
        elif event.ev_type == "Absolute":
            self.process_stick(event)

    def toggle_torque_slider_pan_tilt(self, enable):
        """Aktiviert/Deaktiviert das Drehmoment für Slider, Pan und Tilt."""
        print(f"toggle_torque_slider_pan_tilt aufgerufen mit enable={enable}")  # Debugging-Ausgabe
        for motor in ["slider", "pan", "tilt"]:
            if enable:
                print(f"Aktiviere Torque für {motor}")  # Debugging-Ausgabe
                self.controller.enable_torque(MOTOR_IDS[motor])
                self.torque_enabled[motor] = True
            else:
                print(f"Deaktiviere Torque für {motor}")  # Debugging-Ausgabe
                self.controller.disable_torque(MOTOR_IDS[motor])
                self.torque_enabled[motor] = False

    def toggle_torque_turntable(self, enable):
        """Aktiviert/Deaktiviert das Drehmoment für den Drehteller."""
        print(f"toggle_torque_turntable aufgerufen mit enable={enable}")  # Debugging-Ausgabe
        if enable:
            print("Aktiviere Torque für Drehteller")  # Debugging-Ausgabe
            self.controller.enable_torque(MOTOR_IDS["turntable"])
            self.torque_enabled["turntable"] = True
        else:
            print("Deaktiviere Torque für Drehteller")  # Debugging-Ausgabe
            self.controller.disable_torque(MOTOR_IDS["turntable"])
            self.torque_enabled["turntable"] = False

    def process_stick(self, event):
        """Verarbeitet Analogstickbewegungen."""
        if event.code in ["ABS_X", "ABS_Y"]:
            axis_value = event.state / 32767.0  # Normalisieren
            motor = "pan" if event.code == "ABS_X" else "tilt"
            velocity = int(axis_value * self.max_velocity)
            print(f"Motor {motor}, Achsenwert: {axis_value}, Geschwindigkeit: {velocity}")  # Debugging
            self.controller.set_goal_velocity(MOTOR_IDS[motor], velocity)
        elif event.code in ["ABS_RX", "ABS_RY"]:
            axis_value = event.state / 32767.0  # Normalisieren
            velocity = int(axis_value * self.max_velocity)
            print(f"Slider, Achsenwert: {axis_value}, Geschwindigkeit: {velocity}")  # Debugging
            self.controller.set_goal_velocity(MOTOR_IDS["slider"], velocity)

    def increase_rpm(self):
        """Erhöht die Geschwindigkeit (RPM) des Drehtellers."""
        self.rpm = min(self.rpm + 10, 1023)
        self.controller.set_goal_velocity(MOTOR_IDS["turntable"], self.rpm)

    def decrease_rpm(self):
        """Verringert die Geschwindigkeit (RPM) des Drehtellers."""
        self.rpm = max(self.rpm - 10, -1023)
        self.controller.set_goal_velocity(MOTOR_IDS["turntable"], self.rpm)

    def center_motors(self):
        """Bewegt die Motoren langsam in die Mittelposition."""
        for motor, limits in MOTOR_LIMITS.items():
            mid_position = (limits["min"] + limits["max"]) // 2
            print(f"Zentriere Motor {motor} auf Position {mid_position}")  # Debugging-Ausgabe
            self.controller.set_goal_position(MOTOR_IDS[motor], mid_position, motor)
            time.sleep(0.5)

    def stop(self):
        """Beendet den Controller-Thread."""
        self.running = False

if __name__ == "__main__":
    controller = MotorController()
    xbox = XboxController(controller)
    xbox.start_controller_thread()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        xbox.stop()
        controller.close()
