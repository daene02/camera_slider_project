#!/usr/bin/env python3
import time
import logging

# Eigene Module
from settings import (
    DEVICE_NAME,
    BAUD_RATE,
    PROTOCOL_VERSION,
    DXL_IDS,
    MOTOR_IDS,
    MOTOR_NAMES,
    MAX_CURRENT_LIMITS,
)
from hardware.dynamixel_registers_reference import DYNAMIXEL_REGISTERS
from dxl_manager import DynamixelManager

logger = logging.getLogger(__name__)

def detect_and_configure_motors():
    """
    1) Initialisiert den DynamixelManager
    2) Liest für jede erwartete ID die Model Number aus
    3) Wählt das richtige Register-Set aus dynamixel_registers_reference
    4) Setzt ggf. Parameter wie Baudrate, Limits, Operating Mode, etc.
    """
    logger.info("Starte Dynamixel-Initialisierung...")

    # Erzeuge Manager mit aktuellen Einstellungen (Port, Baud, Protokoll, IDs...)
    dxl_mgr = DynamixelManager(
        device_name=DEVICE_NAME,
        baud_rate=BAUD_RATE,
        protocol_version=PROTOCOL_VERSION,
        servo_ids=DXL_IDS
    )

    # Du kannst hier ggf. erst einmal scannen, ob alle IDs antworten,
    # oder ob es unbekannte IDs gibt. Wir gehen davon aus, dass DXL_IDS = [1,2,3,...]
    # schon korrekt ist.

    # Adressen für das Auslesen der Model Number in den meisten X-Servos = 0~1
    # (Manche Protokoll-2.0-Servos haben MODEL_NUMBER an Adresse 0, 2 Bytes)
    MODEL_NUMBER_ADDR = 0
    MODEL_NUMBER_LEN  = 2

    for dxl_id in DXL_IDS:
        # Lies die Model Number (2 Byte) über Read
        result, model_number = read_model_number(dxl_mgr, dxl_id, MODEL_NUMBER_ADDR, MODEL_NUMBER_LEN)
        if not result:
            logger.error(f"Motor ID {dxl_id} antwortet nicht oder Fehler beim Lesen der Model Number.")
            continue

        # Finde heraus, welches Modell (XM430, XL430, XM540, etc.) zur model_number passt
        # Normalerweise müsstest du eine Map haben: z.B. 1020 = XM430-W350, etc.
        model_type = match_model_number_to_name(model_number)

        if not model_type:
            logger.warning(f"Unbekannter Modelltyp (Number={model_number}) für ID {dxl_id}.")
            continue

        logger.info(f"ID {dxl_id} hat Modelltyp: {model_type}")

        # Lade passendes Register-Set aus DYNAMIXEL_REGISTERS
        if model_type in DYNAMIXEL_REGISTERS:
            reg = DYNAMIXEL_REGISTERS[model_type]
        else:
            logger.warning(f"Kein Register-Eintrag für '{model_type}' gefunden.")
            continue

        # Beispiel: Du könntest jetzt "Baudrate" / Operating Mode setzen,
        # indem du auf reg['OPERATING_MODE'] schreibst etc.
        # Hier nur zur Demo ein Write auf den Operating Mode:
        set_operating_mode(dxl_mgr, dxl_id, reg)

        # Falls du im Projekt dynamisch die Baudrate ändern möchtest,
        # kannst du so was machen:
        # set_baud_rate(dxl_mgr, dxl_id, reg, desired_baud=1000000)

        # Optional: Stromlimit einstellen
        # Du könntest hier MAX_CURRENT_LIMITS[MOTOR_NAMES[dxl_id]] abrufen.
        # set_current_limit(dxl_mgr, dxl_id, reg, current_limit=300)

    logger.info("Alle Motoren wurden abgefragt und konfiguriert.")
    dxl_mgr.close()


def read_model_number(dxl_mgr, dxl_id, address, length):
    """
    Liest die Model Number (2 Bytes) aus dem Servo-Speicher.
    """
    # Wir nutzen hier ein normales Read, nicht BulkRead.
    # (Für BulkRead könntest du groupBulkRead verwenden.)
    from dynamixel_sdk import COMM_SUCCESS

    # Send Read Request
    result, error = dxl_mgr.packetHandler.read2ByteTxRx(dxl_mgr.portHandler, dxl_id, address)
    if dxl_mgr.packetHandler.getLastTxRxResult() != COMM_SUCCESS:
        return False, None
    return True, result


def match_model_number_to_name(model_number):
    """
    Mappt die model_number (z.B. 1030, 1060, ...) zum tatsächlichen Modellnamen
    (z.B. 'XM430-W350-T').
    Modellnummern findest du im eManual von Robotis.
    Z.B. XM430-W350-T = 1030, XM430-W210-T = 1020, etc.
    """
    # Beispiel (Zahlen erfunden!):
    model_map = {
        1020: "XM430-W210",
        1030: "XM430-W350-T",
        1060: "XL430-W250-T",
        1130: "XM540-W270-T",
        # Füge hier deine echten Model Numbers an
    }

    return model_map.get(model_number, None)


def set_operating_mode(dxl_mgr, dxl_id, reg):
    """
    Beispiel-Funktion: Setzt Operating Mode = Position Control (3)
    oder Multi-Turn etc., basierend auf dem Registerset.
    """
    from dynamixel_sdk import COMM_SUCCESS

    # Operating Mode = 3 (Position Control Mode) in X-Serie
    # oder 1 = Velocity Mode, etc. Siehe eManual
    desired_mode = 3

    # Adressen:
    oper_mode_addr = reg.get('OPERATING_MODE', 11)

    # 1 Byte Write
    dxl_mgr.packetHandler.write1ByteTxRx(dxl_mgr.portHandler, dxl_id, oper_mode_addr, desired_mode)

    if dxl_mgr.packetHandler.getLastTxRxResult() != COMM_SUCCESS:
        logger.error(f"Fehler beim Setzen des Operating Mode für ID {dxl_id}.")


def set_baud_rate(dxl_mgr, dxl_id, reg, desired_baud=1000000):
    """
    Beispiel-Funktion: Ändert dynamisch die Baudrate eines Servos.
    Achtung: Danach musst du i.d.R. deinen Port neu öffnen mit dem neuen Baud-Wert.
    """
    from dynamixel_sdk import COMM_SUCCESS

    # Die Adresse für Baud Rate kann variieren, z.B. 8 (Protocol 2.0, X-Serie)
    # laut eManual: Adress=8, 1Byte: Value => 1=1Mbps, 3=1Mbps? (Hängt vom eManual ab)
    # Siehe Robotis-Manual \"Baud Rate\" Table
    # Hier nur Demo:
    #   1 => 1Mbps, 3 => 1Mbps, 4 => 2Mbps, etc.
    # => Du musst das anpassen, je nachdem was Robotis definiert.
    baud_rate_addr = 8  # Demo

    # Wandle desired_baud in Robotis-Value
    # Das hier ist sehr vereinfacht; du müsstest ggf. eine Lookup-Tabelle machen:
    # {9600: 207, 57600: 34, 115200: 16, 1000000: 3, 2000000: 4, ...}
    # Hier nur Hardcode:
    baud_value_map = {
        9600: 207,
        57600: 34,
        115200: 16,
        1000000: 3,
        2000000: 4,
    }
    if desired_baud not in baud_value_map:
        logger.error(f\"Baudrate {desired_baud} nicht in Map definiert.\")
        return

    param_baud = baud_value_map[desired_baud]

    dxl_mgr.packetHandler.write1ByteTxRx(dxl_mgr.portHandler, dxl_id, baud_rate_addr, param_baud)
    if dxl_mgr.packetHandler.getLastTxRxResult() != COMM_SUCCESS:
        logger.error(f\"Fehler beim Setzen der Baudrate für ID {dxl_id}.\")
    else:
        logger.info(f\"Baudrate für ID {dxl_id} auf {desired_baud} gesetzt.\")
        # Wichtig: Du musst jetzt dein dxl_mgr-Port neu auf desired_baud setzen
        # dxl_mgr.portHandler.closePort()
        # dxl_mgr.portHandler.setBaudRate(desired_baud)
        # dxl_mgr.portHandler.openPort()
        # -> Ab hier kommunizierst du mit dem neuen Baud


def set_current_limit(dxl_mgr, dxl_id, reg, current_limit=300):
    """
    Beispielfunktion, um das CURRENT_LIMIT zu schreiben,
    z.B. um Überlastung zu vermeiden.
    """
    from dynamixel_sdk import COMM_SUCCESS

    current_limit_addr = reg.get('CURRENT_LIMIT', 38)  # 2 Byte
    lowbyte = current_limit & 0xFF
    highbyte = (current_limit >> 8) & 0xFF
    dxl_mgr.packetHandler.write2ByteTxRx(dxl_mgr.portHandler, dxl_id, current_limit_addr, (highbyte << 8) | lowbyte)
    if dxl_mgr.packetHandler.getLastTxRxResult() != COMM_SUCCESS:
        logger.error(f\"Fehler beim Setzen des Current Limits für ID {dxl_id}.\")
    else:
        logger.info(f\"Current Limit für ID {dxl_id} auf {current_limit} gesetzt.\")


def main():
    logging.info(\"Starte das Programm...\")
    detect_and_configure_motors()
    logging.info(\"Programm beendet.\")


if __name__ == \"__main__\":
    main()
