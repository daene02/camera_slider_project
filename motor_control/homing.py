from dynamixel_sdk import PortHandler, PacketHandler
from settings import *

class HomingController:
    def __init__(self, port_handler, packet_handler):
        self.port_handler = port_handler
        self.packet_handler = packet_handler

    def execute_homing(self):
        slider_id = MOTOR_IDS.get("slider")
        if not slider_id:
            print("Fehler: Keine Motor-ID für Slider gefunden.")
            return

        print("Setze aktuellen Punkt als Nullpunkt für Slider...")
        result, comm_result, error = self.packet_handler.read4ByteTxRx(self.port_handler, slider_id, PRESENT_POSITION)
        if comm_result == 0 and error == 0:
            current_position = result
            print(f"Aktuelle Position: {current_position}")

            offset_value = -current_position if current_position > 0 else abs(current_position)
            print(f"Berechneter Offset-Wert: {offset_value}")

            try:
                write_result = self.packet_handler.write4ByteTxRx(self.port_handler, slider_id, HOMING_OFFSET, offset_value)
                if len(write_result) == 2:  # Nur comm_result und error zurückgegeben
                    comm_result, error = write_result
                elif len(write_result) == 3:  # Ergebnis korrekt zurückgegeben
                    result, comm_result, error = write_result
                else:
                    raise ValueError("Unerwartete Rückgabe von write4ByteTxRx")

                if comm_result != 0 or error != 0:
                    print(f"Fehler beim Setzen des Offsets: comm_result={comm_result}, error={error}")
                    return
                print("Offset erfolgreich gesetzt.")
            except Exception as e:
                print(f"Fehler beim Setzen des Offsets: {e}")
        else:
            print(f"Fehler beim Lesen der aktuellen Position: comm_result={comm_result}, error={error}")

        print("Homing abgeschlossen.")
