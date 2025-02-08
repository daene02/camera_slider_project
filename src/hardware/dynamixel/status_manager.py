"""Status-Abfragen für Dynamixel Servos"""

from dynamixel_sdk import (
    GroupBulkRead,
    COMM_SUCCESS
)
from .constants import *
from .base_manager import DynamixelBaseManager

class DynamixelStatusManager(DynamixelBaseManager):
    def bulk_read_temperature(self):
        """Liest die Temperatur aller Servos"""
        with self.lock:
            try:
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
        """Liest die Spannung aller Servos"""
        with self.lock:
            try:
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
        """
        Liest den Strom aller Servos und konvertiert ihn in Ampere
        """
        with self.lock:
            try:
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
                        
                        # Konvertiere unsigned 16-bit zu signed 16-bit
                        if raw_value > 32767:
                            raw_value -= 65536  # Umwandlung in negative Werte
                            raw_value *= -1     # Umdrehen der negativen Werte

                        # Umrechnung in Ampere
                        CURRENT_SCALE_FACTOR = 0.01  # 1 Einheit = 1 mA
                        current = raw_value * CURRENT_SCALE_FACTOR
                        
                        curr_dict[dxl_id] = current
        
                    else:
                        curr_dict[dxl_id] = None
            
                grp_read.clearParam()
                return curr_dict
            except Exception as e:
                print(f"[ERROR] BulkRead Current error: {e}")
                return {}
