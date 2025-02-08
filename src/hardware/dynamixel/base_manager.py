"""Basis-Kommunikation mit Dynamixel Servos"""

from threading import Lock
from dynamixel_sdk import (
    PortHandler,
    PacketHandler,
    GroupBulkRead,
    GroupBulkWrite,
    COMM_SUCCESS
)
from .constants import *

class DynamixelBaseManager:
    def __init__(self, device=DEVICENAME, baud=BAUDRATE, protocol=PROTOCOL_VERSION, dxl_ids=DXL_IDS):
        self.dxl_ids = dxl_ids
        self.portHandler = PortHandler(device)
        self.packetHandler = PacketHandler(protocol)
        self.lock = Lock()

        if not self.portHandler.openPort():
            raise IOError(f"Failed to open port ({device}).")
        if not self.portHandler.setBaudRate(baud):
            raise IOError(f"Failed to set baudrate ({baud}).")

        self.groupBulkRead = GroupBulkRead(self.portHandler, self.packetHandler)
        self.groupBulkWrite = GroupBulkWrite(self.portHandler, self.packetHandler)

    def enable_torque(self, motor_ids=None):
        """Aktiviert das Drehmoment für die angegebenen Motoren"""
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
        """Deaktiviert das Drehmoment für die angegebenen Motoren"""
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
        """Liest den Torque-Enable-Status aller Motoren"""
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

    def close(self):
        """Schließt die Kommunikation mit den Servos"""
        self.portHandler.closePort()
