from motor_control import MotorController
from settings import MOTOR_IDS, PID_DEFAULTS

class PIDTuner:
    def __init__(self, controller):
        self.controller = controller

    def read_pid_values(self, motor_id):
        print(f"Lese aktuelle PID-Werte für Motor ID {motor_id}...")
        velocity_i_gain = self.controller.packet_handler.read2ByteTxRx(self.controller.port_handler, motor_id, 76)[0]
        velocity_p_gain = self.controller.packet_handler.read2ByteTxRx(self.controller.port_handler, motor_id, 78)[0]
        position_d_gain = self.controller.packet_handler.read2ByteTxRx(self.controller.port_handler, motor_id, 80)[0]
        position_i_gain = self.controller.packet_handler.read2ByteTxRx(self.controller.port_handler, motor_id, 82)[0]
        position_p_gain = self.controller.packet_handler.read2ByteTxRx(self.controller.port_handler, motor_id, 84)[0]

        return {
            "velocity_i_gain": velocity_i_gain,
            "velocity_p_gain": velocity_p_gain,
            "position_d_gain": position_d_gain,
            "position_i_gain": position_i_gain,
            "position_p_gain": position_p_gain
        }

    def write_pid_values(self, motor_id, pid_values):
        print(f"Schreibe neue PID-Werte für Motor ID {motor_id}...")
        self.controller.packet_handler.write2ByteTxRx(self.controller.port_handler, motor_id, 76, pid_values["velocity_i_gain"])
        self.controller.packet_handler.write2ByteTxRx(self.controller.port_handler, motor_id, 78, pid_values["velocity_p_gain"])
        self.controller.packet_handler.write2ByteTxRx(self.controller.port_handler, motor_id, 80, pid_values["position_d_gain"])
        self.controller.packet_handler.write2ByteTxRx(self.controller.port_handler, motor_id, 82, pid_values["position_i_gain"])
        self.controller.packet_handler.write2ByteTxRx(self.controller.port_handler, motor_id, 84, pid_values["position_p_gain"])

    def tune_pid(self):
        for motor_name, motor_id in MOTOR_IDS.items():
            print(f"\n=== Bearbeite Motor: {motor_name} (ID: {motor_id}) ===")
            
            # Alte Werte lesen
            old_pid_values = self.read_pid_values(motor_id)
            print(f"Alte PID-Werte: {old_pid_values}")

            # Neue Werte aus settings.py nehmen
            new_pid_values = PID_DEFAULTS[motor_name]
            print(f"Schreibe neue PID-Werte: {new_pid_values}")
            self.write_pid_values(motor_id, new_pid_values)

            # Neue Werte aus Motor lesen
            updated_pid_values = self.read_pid_values(motor_id)
            print(f"Aktualisierte PID-Werte: {updated_pid_values}")

if __name__ == "__main__":
    controller = MotorController()
    tuner = PIDTuner(controller)

    try:
        tuner.tune_pid()
    finally:
        controller.close()
