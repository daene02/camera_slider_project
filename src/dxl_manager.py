#!/usr/bin/env python3
# dxl_manager.py
import time
import sys
from threading import Lock
from dynamixel_sdk import (
    PortHandler,
    PacketHandler,
    GroupBulkRead,
    GroupBulkWrite,
    DXL_LOBYTE,
    DXL_HIBYTE,
    DXL_LOWORD,
    DXL_HIWORD,
    COMM_SUCCESS
)

# Beispiel-Register (X-Serie, Protocol 2.0)
ADDR_PRO_TORQUE_ENABLE         = 64
ADDR_PRO_GOAL_POSITION         = 116
ADDR_PRO_PRESENT_POSITION      = 132
ADDR_PRO_PROFILE_ACCEL         = 108
ADDR_PRO_PROFILE_VELOC         = 112
ADDR_PRO_PRESENT_TEMPERATURE   = 146
ADDR_PRO_PRESENT_VOLTAGE       = 144
ADDR_PRO_PRESENT_CURRENT       = 126

LEN_PRO_GOAL_POSITION          = 4
LEN_PRO_PRESENT_POSITION       = 4
LEN_PRO_PROFILE_PARAM          = 4
LEN_PRO_PRESENT_TEMPERATURE    = 1
LEN_PRO_PRESENT_VOLTAGE        = 2
LEN_PRO_PRESENT_CURRENT        = 2

PROTOCOL_VERSION               = 2.0
BAUDRATE                       = 57600
DEVICENAME                     = "/dev/ttyUSB0"

DXL_IDS                        = [1, 2, 3, 4, 5, 6]

class DynamixelManager:
    def __init__(self, device=DEVICENAME, baud=BAUDRATE, protocol=PROTOCOL_VERSION, dxl_ids=DXL_IDS):
        self.dxl_ids = dxl_ids
        self.portHandler = PortHandler(device)
        self.packetHandler = PacketHandler(protocol)
        self.lock = Lock()  # Add lock for thread safety

        if not self.portHandler.openPort():
            raise IOError(f"Failed to open port ({device}).")
        if not self.portHandler.setBaudRate(baud):
            raise IOError(f"Failed to set baudrate ({baud}).")

        self.groupBulkRead = GroupBulkRead(self.portHandler, self.packetHandler)
        self.groupBulkWrite = GroupBulkWrite(self.portHandler, self.packetHandler)

    def enable_torque(self, motor_ids=None):
        with self.lock:
            if motor_ids is None:
                motor_ids = self.dxl_ids
            
            for dxl_id in motor_ids:
                result, error = self.packetHandler.write1ByteTxRx(
                    self.portHandler, dxl_id, ADDR_PRO_TORQUE_ENABLE, 1
                )
                if result != COMM_SUCCESS:
                    print(f"[ERROR] TorqueEnable txrx: {self.packetHandler.getTxRxResult(result)}")
                elif error != 0:
                    print(f"[ERROR] TorqueEnable: {self.packetHandler.getRxPacketError(error)}")

    def disable_torque(self, motor_ids=None):
        with self.lock:
            if motor_ids is None:
                motor_ids = self.dxl_ids
            
            for dxl_id in motor_ids:
                result, error = self.packetHandler.write1ByteTxRx(
                    self.portHandler, dxl_id, ADDR_PRO_TORQUE_ENABLE, 0
                )
                if result != COMM_SUCCESS:
                    print(f"[ERROR] TorqueDisable txrx: {self.packetHandler.getTxRxResult(result)}")
                elif error != 0:
                    print(f"[ERROR] TorqueDisable: {self.packetHandler.getRxPacketError(error)}")

    def bulk_read_torque_enable(self):
        with self.lock:
            try:
                grp_read = GroupBulkRead(self.portHandler, self.packetHandler)
                for dxl_id in self.dxl_ids:
                    ok = grp_read.addParam(dxl_id, ADDR_PRO_TORQUE_ENABLE, 1)
                    if not ok:
                        print(f"[WARN] Konnte ID {dxl_id} nicht für Torque Enable registrieren.")

                result = grp_read.txRxPacket()
                if result != COMM_SUCCESS:
                    print(f"[ERROR] BulkRead Torque Enable: {self.packetHandler.getTxRxResult(result)}")

                torque_dict = {}
                for dxl_id in self.dxl_ids:
                    if grp_read.isAvailable(dxl_id, ADDR_PRO_TORQUE_ENABLE, 1):
                        val = grp_read.getData(dxl_id, ADDR_PRO_TORQUE_ENABLE, 1)
                        torque_dict[dxl_id] = (val == 1)
                    else:
                        torque_dict[dxl_id] = False

                grp_read.clearParam()
                return torque_dict
            except Exception as e:
                print(f"[ERROR] BulkRead Torque Enable error: {e}")
                return {}

    def bulk_read_positions(self):
        with self.lock:  # Acquire lock before port access
            """
            Liest die Present Position (4 Byte) aller Servos.
            """
            self.groupBulkRead.clearParam()
            for dxl_id in self.dxl_ids:
                success = self.groupBulkRead.addParam(dxl_id, ADDR_PRO_PRESENT_POSITION, LEN_PRO_PRESENT_POSITION)
                if not success:
                    print(f"[WARN] Konnte ID {dxl_id} nicht für Present Position registrieren.")

            dxl_comm_result = self.groupBulkRead.txRxPacket()
            if dxl_comm_result != COMM_SUCCESS:
                print(f"[ERROR] BulkRead Positions: {self.packetHandler.getTxRxResult(dxl_comm_result)}")

            positions = {}
            for dxl_id in self.dxl_ids:
                if self.groupBulkRead.isAvailable(dxl_id, ADDR_PRO_PRESENT_POSITION, LEN_PRO_PRESENT_POSITION):
                    data = self.groupBulkRead.getData(dxl_id, ADDR_PRO_PRESENT_POSITION, LEN_PRO_PRESENT_POSITION)
                    positions[dxl_id] = data
                else:
                    positions[dxl_id] = None
            return positions

    def bulk_write_goal_positions(self, goal_dict):
        with self.lock:  # Acquire lock before port access
            try:
                """
                goal_dict = {dxl_id: goal_position}
                """
                self.groupBulkWrite.clearParam()
                for dxl_id, goal_pos in goal_dict.items():
                    param_goal_pos = [
                        DXL_LOBYTE(DXL_LOWORD(goal_pos)),
                        DXL_HIBYTE(DXL_LOWORD(goal_pos)),
                        DXL_LOBYTE(DXL_HIWORD(goal_pos)),
                        DXL_HIBYTE(DXL_HIWORD(goal_pos))
                    ]
                    success = self.groupBulkWrite.addParam(dxl_id, ADDR_PRO_GOAL_POSITION, LEN_PRO_GOAL_POSITION, param_goal_pos)
                    if not success:
                        print(f"[WARN] Konnte Goal-Position für ID {dxl_id} nicht hinzufügen.")

                dxl_comm_result = self.groupBulkWrite.txPacket()
                if dxl_comm_result != COMM_SUCCESS:
                    print(f"[ERROR] BulkWrite GoalPositions: {self.packetHandler.getTxRxResult(dxl_comm_result)}")
                self.groupBulkWrite.clearParam()
                return True
            except Exception as e:
                print(f"[ERROR] BulkWrite GoalPositions error: {e}")
                return False

    def bulk_read_profile_acceleration(self):
        """
        Liest Profile Acceleration (4 Byte).
        """
        grp_read = GroupBulkRead(self.portHandler, self.packetHandler)
        for dxl_id in self.dxl_ids:
            ok = grp_read.addParam(dxl_id, ADDR_PRO_PROFILE_ACCEL, LEN_PRO_PROFILE_PARAM)
            if not ok:
                print(f"[WARN] Konnte ID {dxl_id} nicht für Profile Accel registrieren.")

        result = grp_read.txRxPacket()
        if result != COMM_SUCCESS:
            print(f"[ERROR] BulkRead Profile Accel: {self.packetHandler.getTxRxResult(result)}")

        accel_dict = {}
        for dxl_id in self.dxl_ids:
            if grp_read.isAvailable(dxl_id, ADDR_PRO_PROFILE_ACCEL, LEN_PRO_PROFILE_PARAM):
                val = grp_read.getData(dxl_id, ADDR_PRO_PROFILE_ACCEL, LEN_PRO_PROFILE_PARAM)
                accel_dict[dxl_id] = val
            else:
                accel_dict[dxl_id] = None

        grp_read.clearParam()
        return accel_dict

    def bulk_read_profile_velocity(self):
        """
        Liest Profile Velocity (4 Byte).
        """
        grp_read = GroupBulkRead(self.portHandler, self.packetHandler)
        for dxl_id in self.dxl_ids:
            ok = grp_read.addParam(dxl_id, ADDR_PRO_PROFILE_VELOC, LEN_PRO_PROFILE_PARAM)
            if not ok:
                print(f"[WARN] Konnte ID {dxl_id} nicht für Profile Velocity registrieren.")

        result = grp_read.txRxPacket()
        if result != COMM_SUCCESS:
            print(f"[ERROR] BulkRead Profile Veloc: {self.packetHandler.getTxRxResult(result)}")

        veloc_dict = {}
        for dxl_id in self.dxl_ids:
            if grp_read.isAvailable(dxl_id, ADDR_PRO_PROFILE_VELOC, LEN_PRO_PROFILE_PARAM):
                val = grp_read.getData(dxl_id, ADDR_PRO_PROFILE_VELOC, LEN_PRO_PROFILE_PARAM)
                veloc_dict[dxl_id] = val
            else:
                veloc_dict[dxl_id] = None

        grp_read.clearParam()
        return veloc_dict

    def bulk_write_profile_acceleration(self, accel_dict):
        with self.lock:  # Acquire lock before port access
            try:
                self.groupBulkWrite.clearParam()
                for dxl_id, acc_val in accel_dict.items():
                    param_data = [
                        DXL_LOBYTE(DXL_LOWORD(acc_val)),
                        DXL_HIBYTE(DXL_LOWORD(acc_val)),
                        DXL_LOBYTE(DXL_HIWORD(acc_val)),
                        DXL_HIBYTE(DXL_HIWORD(acc_val))
                    ]
                    ok = self.groupBulkWrite.addParam(dxl_id, ADDR_PRO_PROFILE_ACCEL, LEN_PRO_PROFILE_PARAM, param_data)
                    if not ok:
                        print(f"[WARN] Konnte Profile Accel für ID {dxl_id} nicht hinzufügen.")

                result = self.groupBulkWrite.txPacket()
                if result != COMM_SUCCESS:
                    print(f"[ERROR] BulkWrite Profile Accel: {self.packetHandler.getTxRxResult(result)}")
                self.groupBulkWrite.clearParam()
                return True
            except Exception as e:
                print(f"[ERROR] BulkWrite Profile Acceleration error: {e}")
                return False

    def bulk_write_profile_velocity(self, veloc_dict):
        with self.lock:  # Acquire lock before port access
            try:
                self.groupBulkWrite.clearParam()
                for dxl_id, vel_val in veloc_dict.items():
                    param_data = [
                        DXL_LOBYTE(DXL_LOWORD(vel_val)),
                        DXL_HIBYTE(DXL_LOWORD(vel_val)),
                        DXL_LOBYTE(DXL_HIWORD(vel_val)),
                        DXL_HIBYTE(DXL_HIWORD(vel_val))
                    ]
                    ok = self.groupBulkWrite.addParam(dxl_id, ADDR_PRO_PROFILE_VELOC, LEN_PRO_PROFILE_PARAM, param_data)
                    if not ok:
                        print(f"[WARN] Konnte Profile Velocity für ID {dxl_id} nicht hinzufügen.")

                result = self.groupBulkWrite.txPacket()
                if result != COMM_SUCCESS:
                    print(f"[ERROR] BulkWrite Profile Velocity: {self.packetHandler.getTxRxResult(result)}")
                self.groupBulkWrite.clearParam()
                return True
            except Exception as e:
                print(f"[ERROR] BulkWrite Profile Velocity error: {e}")
                return False

    def bulk_read_temperature(self):
        with self.lock:  # Acquire lock before port access
            try:
                """
                Liest die Temperatur (1 Byte).
                """
                grp_read = GroupBulkRead(self.portHandler, self.packetHandler)
                for dxl_id in self.dxl_ids:
                    ok = grp_read.addParam(dxl_id, ADDR_PRO_PRESENT_TEMPERATURE, LEN_PRO_PRESENT_TEMPERATURE)
                    if not ok:
                        print(f"[WARN] Konnte ID {dxl_id} nicht für Present Temperature registrieren.")

                result = grp_read.txRxPacket()
                if result != COMM_SUCCESS:
                    print(f"[ERROR] BulkRead Temperature: {self.packetHandler.getTxRxResult(result)}")

                temp_dict = {}
                for dxl_id in self.dxl_ids:
                    if grp_read.isAvailable(dxl_id, ADDR_PRO_PRESENT_TEMPERATURE, LEN_PRO_PRESENT_TEMPERATURE):
                        val = grp_read.getData(dxl_id, ADDR_PRO_PRESENT_TEMPERATURE, LEN_PRO_PRESENT_TEMPERATURE)
                        temp_dict[dxl_id] = val
                    else:
                        temp_dict[dxl_id] = None

                grp_read.clearParam()
                return temp_dict
            except Exception as e:
                print(f"[ERROR] BulkRead Temperature error: {e}")
                return {}

    def bulk_read_voltage(self):
        with self.lock:  # Acquire lock before port access
            try:
                """
                Liest die Spannung (2 Byte).
                """
                grp_read = GroupBulkRead(self.portHandler, self.packetHandler)
                for dxl_id in self.dxl_ids:
                    ok = grp_read.addParam(dxl_id, ADDR_PRO_PRESENT_VOLTAGE, LEN_PRO_PRESENT_VOLTAGE)
                    if not ok:
                        print(f"[WARN] Konnte ID {dxl_id} nicht für Present Voltage registrieren.")

                result = grp_read.txRxPacket()
                if result != COMM_SUCCESS:
                    print(f"[ERROR] BulkRead Voltage: {self.packetHandler.getTxRxResult(result)}")

                volt_dict = {}
                for dxl_id in self.dxl_ids:
                    if grp_read.isAvailable(dxl_id, ADDR_PRO_PRESENT_VOLTAGE, LEN_PRO_PRESENT_VOLTAGE):
                        val = grp_read.getData(dxl_id, ADDR_PRO_PRESENT_VOLTAGE, LEN_PRO_PRESENT_VOLTAGE)
                        volt_dict[dxl_id] = val
                    else:
                        volt_dict[dxl_id] = None

                grp_read.clearParam()
                return volt_dict
            except Exception as e:
                print(f"[ERROR] BulkRead Voltage error: {e}")
                return {}

    def bulk_read_current(self):
        with self.lock:  # Acquire lock before port access
            try:
                """
                Liest den Strom (2 Byte) und konvertiert ihn in Ampere.
                """
                grp_read = GroupBulkRead(self.portHandler, self.packetHandler)
                for dxl_id in self.dxl_ids:
                    ok = grp_read.addParam(dxl_id, ADDR_PRO_PRESENT_CURRENT, LEN_PRO_PRESENT_CURRENT)
                    if not ok:
                        print(f"[WARN] Konnte ID {dxl_id} nicht für Present Current registrieren.")
    
                result = grp_read.txRxPacket()
                if result != COMM_SUCCESS:
                    print(f"[ERROR] BulkRead Current: {self.packetHandler.getTxRxResult(result)}")
    
                curr_dict = {}
                for dxl_id in self.dxl_ids:
                    if grp_read.isAvailable(dxl_id, ADDR_PRO_PRESENT_CURRENT, LEN_PRO_PRESENT_CURRENT):
                        raw_value = grp_read.getData(dxl_id, ADDR_PRO_PRESENT_CURRENT, LEN_PRO_PRESENT_CURRENT)
                        
                        # Überprüfung auf Fehlerwerte
                        if raw_value >= 65540:  # Fehlerhafter Wert nahe 65535 erkannt
                            print(f"[WARN] Ungültiger Wert für ID {dxl_id}: {raw_value}")
                            curr_dict[dxl_id] = None
                        else:
                            # Korrektur für negative Werte und Umkehrung nur für Werte über 1023
                            if raw_value > 1024:
                                raw_value -= 2048  # Umwandlung für negative Ströme
                                raw_value *= -1  # Umdrehen nur der negativen Werte
                            
                            # Umrechnung des Rohwerts in Ampere
                            CURRENT_SCALE_FACTOR = 1  # Beispiel: 1 Einheit = 1 mA
                            current = raw_value * CURRENT_SCALE_FACTOR  # Berechnung des Stroms in Ampere
                            
                            curr_dict[dxl_id] = current  # Speichern des berechneten Stroms
    
                    else:
                        curr_dict[dxl_id] = None
    
                grp_read.clearParam()
                return curr_dict
            except Exception as e:
                print(f"[ERROR] BulkRead Current error: {e}")
                return {}








    

    



    



    
    














    

    




                grp_read.clearParam()
                return curr_dict
            except Exception as e:
                print(f"[ERROR] BulkRead Current error: {e}")
                return {}


    def close(self):
        self.portHandler.closePort()

if __name__ == "__main__":
    manager = DynamixelManager()
    manager.enable_torque()

    # Beispiel: Positionen schreiben
    manager.bulk_write_goal_positions({1: 500, 2: 1500})
    time.sleep(2)

    # Auslesen
    pos_data = manager.bulk_read_positions()
    print("Positions:", pos_data)

    acc_data = manager.bulk_read_profile_acceleration()
    vel_data = manager.bulk_read_profile_velocity()
    print("Accel:", acc_data)
    print("Velocity:", vel_data)

    temp_data = manager.bulk_read_temperature()
    volt_data = manager.bulk_read_voltage()
    curr_data = manager.bulk_read_current()

    print("Temperature:", temp_data)
    print("Voltage:", volt_data)
    print("Current:", curr_data)

    manager.disable_torque()
    manager.close()
