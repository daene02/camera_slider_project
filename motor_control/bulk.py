import logging
import os
import sys
import time
import json
import settings
from dynamixel_sdk import PortHandler, PacketHandler, GroupBulkRead, GroupBulkWrite, DXL_LOBYTE, DXL_LOWORD, DXL_HIBYTE, DXL_HIWORD, COMM_SUCCESS
from settings import *

PROFILES_FILE = "/home/pi/camera_slider_project/profiles/profiles.json"

def convert_position(motor_id, position):
    factor = 0.015 if MOTOR_NAMES[motor_id] == "slider" else 0.0878906
    converted = round(position * factor, 1)
    logging.debug(f"Position für Motor {MOTOR_NAMES[motor_id]}: {position} umgerechnet zu {converted}.")
    return converted

def convert_current(current):
    if isinstance(current, int):
        converted = round(current * 2.69, 1)
        logging.debug(f"Strom umgerechnet: {current} zu {converted} mA.")
        return converted
    logging.debug("Ungültiger Stromwert: N/A zurückgegeben.")
    return "N/A"

def convert_voltage(voltage):
    converted = round(voltage / 10, 1)
    logging.debug(f"Spannung umgerechnet: {voltage} zu {converted} V.")
    return converted

class BulkOperations:
    def __init__(self, port_handler, packet_handler):
        self.port_handler = port_handler
        self.packet_handler = packet_handler

    def enable_torque(self, motor_id):
        try:
            result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, 64, 1)
            if result != 0:
                raise Exception(f"Fehler beim Aktivieren des Drehmoments für Motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
            if error != 0:
                raise Exception(f"Fehler beim Aktivieren des Drehmoments für Motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
            print(f"Torque aktiviert für Motor {motor_id}")
        except Exception as e:
            print(f"Fehler in enable_torque: {e}")

    def disable_torque(self, motor_id):
        try:
            result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, 64, 0)
            if result != 0:
                raise Exception(f"Fehler beim Deaktivieren des Drehmoments für Motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
            if error != 0:
                raise Exception(f"Fehler beim Deaktivieren des Drehmoments für Motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
            print(f"Torque deaktiviert für Motor {motor_id}")
        except Exception as e:
            print(f"Fehler in disable_torque: {e}")

    def save_to_file(self, data):
        try:
            formatted_data = {
                motor_id: {
                    "name": MOTOR_NAMES[motor_id],
                    "position_mm_or_deg": convert_position(motor_id, motor_info.get("position", 0)),
                    "temperature_C": motor_info.get("temperature", "N/A"),
                    "current_mA": convert_current(motor_info.get("current", 0)),
                    "voltage_V": convert_voltage(motor_info.get("voltage", 0))
                }
                for motor_id, motor_info in data.items()
            }
            with open(PROFILES_FILE, 'w') as file:
                json.dump(formatted_data, file, indent=4)
                logging.info(f"Daten erfolgreich in {PROFILES_FILE} gespeichert.")
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Daten: {e}")

    def validate_data(self, data):
        validated_data = {}
        for motor_id, motor_info in data.items():
            validated_data[motor_id] = {
                "name": motor_info.get("name", "Unknown"),
                "position": motor_info.get("position", 0) if 0 <= motor_info.get("position", 0) <= 4096 else 0,
                "temperature": motor_info.get("temperature", "N/A") if 0 <= motor_info.get("temperature", 0) <= 100 else "N/A",
                "current": motor_info.get("current", "N/A") if 0 <= motor_info.get("current", 0) <= 1000 else 0,
                "voltage": motor_info.get("voltage", "N/A") if 100 <= motor_info.get("voltage", 0) <= 130 else 0
            }
        return validated_data

    def clean_data(self, data):
        for motor_id, motor_info in data.items():
            motor_info["name"] = motor_info.get("name", "Unknown")
            motor_info["position"] = motor_info.get("position", 0) if 0 <= motor_info.get("position", 0) <= 4096 else 0
            motor_info["temperature"] = motor_info.get("temperature", "N/A") if motor_info.get("temperature") != "N/A" else "N/A"
            motor_info["current"] = motor_info.get("current", "N/A") if motor_info.get("current") != "N/A" else 0
            motor_info["voltage"] = motor_info.get("voltage", "N/A") if motor_info.get("voltage") != "N/A" else 0
        return data

    def bulk_read_all(self, motor_ids):
        logging.info("Starte Bulk-Read...")
        group_bulk_read = GroupBulkRead(self.port_handler, self.packet_handler)

        # Sicherstellen, dass der Port korrekt geöffnet ist
        if not self.port_handler.is_using:
            logging.info("Port ist nicht in Verwendung. Öffne den Port.")
            if not self.port_handler.openPort():
                logging.critical("Port konnte nicht geöffnet werden. Abbruch des Bulk-Write.")
                return

        for motor_id in motor_ids:
            if not group_bulk_read.addParam(motor_id, PRESENT_POSITION, 4):
                logging.warning(f"Parameter für Position für Motor {MOTOR_NAMES[motor_id]} konnte nicht hinzugefügt werden.")

        comm_result = group_bulk_read.txRxPacket()
        if comm_result != COMM_SUCCESS:
            logging.error(f"Bulk-Read fehlgeschlagen: {self.packet_handler.getTxRxResult(comm_result)}")
            return None

        status_data = {}
        for motor_id in motor_ids:
            position = None

            if group_bulk_read.isAvailable(motor_id, PRESENT_POSITION, 4):
                position = group_bulk_read.getData(motor_id, PRESENT_POSITION, 4)
                if not (0 <= position <= 100000):
                    logging.warning(f"Ungültiger Positionswert für Motor {MOTOR_NAMES[motor_id]}: {position}")
                    position = None
            else:
                logging.warning(f"Positionsdaten für Motor {MOTOR_NAMES[motor_id]} nicht verfügbar.")

            # Position umrechnen mit Offset-Berücksichtigung
            motor_name = MOTOR_NAMES[motor_id]
            offset = settings.MOTOR_OFFSETS.get(motor_name, 0)
            
            if position is not None:
                if motor_name == "slider":
                    converted_position = round((position * 0.015) + offset, 1)
                else:
                    converted_position = round((position * 0.0878906) + offset, 1)
            else:
                converted_position = "N/A"

            # Statusdaten speichern
            status_data[motor_id] = {
                "name": motor_name,
                "position": converted_position
            }

        # Port freigeben, um Konflikte zu vermeiden
        if self.port_handler.is_using:
            self.port_handler.closePort()
            logging.info("Port geschlossen, um Konflikte zu vermeiden.")

        group_bulk_read.clearParam()
        logging.info(f"Bulk-Read abgeschlossen: {status_data}")
        return status_data



    def read_individual(self, motor_id):
        try:
            temperature, comm_result, error = self.packet_handler.read1ByteTxRx(self.port_handler, motor_id, PRESENT_TEMPERATURE)
            if comm_result != COMM_SUCCESS or error != 0:
                temperature = None
                logging.warning(f"Fehler beim Lesen der Temperatur von Motor {MOTOR_NAMES[motor_id]}: {self.packet_handler.getTxRxResult(comm_result)}")

            current, comm_result, error = self.packet_handler.read2ByteTxRx(self.port_handler, motor_id, PRESENT_CURRENT)
            if comm_result != COMM_SUCCESS or error != 0:
                current = None
                logging.warning(f"Fehler beim Lesen des Stroms von Motor {MOTOR_NAMES[motor_id]}: {self.packet_handler.getTxRxResult(comm_result)}")

            voltage, comm_result, error = self.packet_handler.read2ByteTxRx(self.port_handler, motor_id, PRESENT_VOLTAGE)
            if comm_result != COMM_SUCCESS or error != 0:
                voltage = None
                logging.warning(f"Fehler beim Lesen der Spannung von Motor {MOTOR_NAMES[motor_id]}: {self.packet_handler.getTxRxResult(comm_result)}")

            # Werte direkt umwandeln
            converted_temperature = temperature if temperature is not None else "N/A"
            converted_current = round(current * 2.69, 1) if current is not None else "N/A"
            converted_voltage = round(voltage / 10, 1) if voltage is not None else "N/A"

            return {
                "temperature": converted_temperature,
                "current": converted_current,
                "voltage": converted_voltage
            }

        except Exception as e:
            logging.error(f"Fehler beim Zugriff auf Motor {MOTOR_NAMES[motor_id]}: {e}")
            return {
                "temperature": "N/A",
                "current": "N/A",
                "voltage": "N/A"
            }

    def bulk_write_all(self, motor_profiles):
        logging.info("Starte Bulk-Write...")
        group_bulk_write = GroupBulkWrite(self.port_handler, self.packet_handler)

        # Sicherstellen, dass der Port korrekt geöffnet ist
        if not self.port_handler.is_using:
            logging.info("Port ist nicht in Verwendung. Öffne den Port.")
            if not self.port_handler.openPort():
                logging.critical("Port konnte nicht geöffnet werden. Abbruch des Bulk-Write.")
                return

        for motor_id, profile in motor_profiles.items():
            goal_position = profile["goal_position"]
            velocity = profile.get("velocity", 0)  # Geschwindigkeit in Schritten/Sekunde
            acceleration = profile.get("acceleration", 0)  # Beschleunigung in Schritten/Sekunde²

            # Debugging: Originalwerte vor Verarbeitung prüfen
            logging.debug(f"Eingaben - Motor ID: {motor_id}, Zielposition: {goal_position}, Geschwindigkeit (Schritte/Sekunde): {velocity}, Beschleunigung (Schritte/Sekunde²): {acceleration}")

            # Offset abziehen, falls Pan oder Tilt
            motor_name = MOTOR_NAMES[motor_id]
            if motor_name in ["pan", "tilt"]:
                offset = settings.MOTOR_OFFSETS.get(motor_name, 0)
                goal_position -= offset

            # Umrechnung von Grad oder mm zurück in Schritte
            conversion_factor = settings.CONVERSION_FACTORS.get(motor_name, 1)
            goal_position_steps = int(goal_position / conversion_factor)

            # Sicherstellen, dass Geschwindigkeit und Beschleunigung im gültigen Bereich liegen
            if not (0 <= velocity <= 32767):
                logging.error(f"Ungültige Geschwindigkeit (Schritte/Sekunde) für Motor {motor_name}: {velocity}")
                continue

            if not (0 <= acceleration <= 32767):
                logging.error(f"Ungültige Beschleunigung (Schritte/Sekunde²) für Motor {motor_name}: {acceleration}")
                continue

            logging.debug(f"Motor: {motor_name}, Zielposition (Schritte): {goal_position_steps}, Geschwindigkeit (Schritte/Sekunde): {velocity}, Beschleunigung (Schritte/Sekunde²): {acceleration}")

            param_goal_position = [
                DXL_LOBYTE(DXL_LOWORD(goal_position_steps)),
                DXL_HIBYTE(DXL_LOWORD(goal_position_steps)),
                DXL_LOBYTE(DXL_HIWORD(goal_position_steps)),
                DXL_HIBYTE(DXL_HIWORD(goal_position_steps))
            ]

            if not group_bulk_write.addParam(motor_id, GOAL_POSITION, len(param_goal_position), bytes(param_goal_position)):
                logging.error(f"Fehler beim Hinzufügen der Zielposition für Motor {motor_name}")

            # Geschwindigkeit (Profile Velocity) direkt setzen
            try:
                if velocity > 32767:
                    velocity = 32767  # Begrenzung auf maximal zulässigen Wert
                param_velocity = [
                    DXL_LOBYTE(DXL_LOWORD(velocity)),
                    DXL_HIBYTE(DXL_LOWORD(velocity)),
                    DXL_LOBYTE(DXL_HIWORD(velocity)),
                    DXL_HIBYTE(DXL_HIWORD(velocity))
                ]
                logging.debug(f"Velocity Bytes: {param_velocity} für Motor {motor_name}")
                result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, PROFILE_VELOCITY, velocity)
                if result != 0 or error != 0:
                    logging.error(f"Direktes Schreiben der Geschwindigkeit (PROFILE_VELOCITY) für Motor {motor_name} fehlgeschlagen: result={result}, error={error}")
                else:
                    logging.debug(f"Direktes Schreiben der Geschwindigkeit erfolgreich für Motor {motor_name}")
            except Exception as e:
                logging.error(f"Fehler bei der Verarbeitung der Geschwindigkeit für Motor {motor_name}: {e}")

            # Beschleunigung (Profile Acceleration) direkt setzen
            try:
                param_acceleration = [
                    DXL_LOBYTE(DXL_LOWORD(acceleration)),
                    DXL_HIBYTE(DXL_LOWORD(acceleration)),
                    DXL_LOBYTE(DXL_HIWORD(acceleration)),
                    DXL_HIBYTE(DXL_HIWORD(acceleration))
                ]
                logging.debug(f"Acceleration Bytes: {param_acceleration} für Motor {motor_name}")
                result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, PROFILE_ACCELERATION, acceleration)
                if result != 0 or error != 0:
                    logging.error(f"Direktes Schreiben der Beschleunigung (PROFILE_ACCELERATION) für Motor {motor_name} fehlgeschlagen: result={result}, error={error}")
                else:
                    logging.debug(f"Direktes Schreiben der Beschleunigung erfolgreich für Motor {motor_name}")
            except Exception as e:
                logging.error(f"Fehler bei der Verarbeitung der Beschleunigung für Motor {motor_name}: {e}")

        comm_result = group_bulk_write.txPacket()
        if comm_result != COMM_SUCCESS:
            logging.error(f"Bulk-Write fehlgeschlagen: {self.packet_handler.getTxRxResult(comm_result)}")
        else:
            logging.info("Bulk-Write erfolgreich abgeschlossen.")

        # Port freigeben, um Konflikte zu vermeiden
        if self.port_handler.is_using:
            self.port_handler.closePort()
            logging.info("Port geschlossen, um Konflikte zu vermeiden.")

        group_bulk_write.clearParam()


# Beispiel zur Initialisierung und Nutzung
if __name__ == "__main__":
    from dynamixel_sdk import PortHandler, PacketHandler

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    port_handler = PortHandler(DEVICENAME)
    packet_handler = PacketHandler(PROTOCOL_VERSION)

    if not port_handler.openPort():
        logging.error("Port konnte nicht geöffnet werden.")
        exit()

    if not port_handler.setBaudRate(BAUDRATE):
        logging.error("Baudrate konnte nicht gesetzt werden.")
        exit()

    bulk_operations = BulkOperations(port_handler, packet_handler)

    motor_ids = MOTOR_IDS.values()

    status_data = bulk_operations.bulk_read_all(motor_ids)
    for motor_id in motor_ids:
        additional_data = bulk_operations.read_individual(motor_id)
        status_data[motor_id].update(additional_data)

    # Validierung der Daten vor dem Speichern
    status_data = bulk_operations.clean_data(status_data)

    bulk_operations.save_to_file(status_data)
    bulk_operations.log_status(status_data)

    motor_profiles = {
        MOTOR_IDS["turntable"]: {"goal_position": 1024},
        MOTOR_IDS["slider"]: {"goal_position": 2048},
        MOTOR_IDS["pan"]: {"goal_position": 512},
        MOTOR_IDS["tilt"]: {"goal_position": 1024},
        MOTOR_IDS["camera_zoom"]: {"goal_position": 4096},
        MOTOR_IDS["turntable_tilt"]: {"goal_position": 3072}
    }

    bulk_operations.bulk_write_all(motor_profiles)

    port_handler.closePort()
