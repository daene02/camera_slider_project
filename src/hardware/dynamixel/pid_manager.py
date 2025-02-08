"""PID-Verwaltung für Dynamixel Servos"""

from dynamixel_sdk import (
    DXL_LOBYTE,
    DXL_HIBYTE,
    DXL_LOWORD,
    DXL_HIWORD,
    COMM_SUCCESS,
    GroupBulkRead,
    GroupBulkWrite
)
import time
from typing import Dict
from .constants import *
from .base_manager import DynamixelBaseManager

class DynamixelPIDManager(DynamixelBaseManager):
    def _validate_velocity_pid(self, gain_type: str, value: int) -> bool:
        """Validiert Velocity PID Parameter"""
        if value < VELOCITY_PID_RANGES[gain_type]['min'] or value > VELOCITY_PID_RANGES[gain_type]['max']:
            print(f"[WARN] {gain_type}-Gain {value} außerhalb des Bereichs")
            return False
        return True

    def bulk_read_pid_parameter(self, address: int) -> Dict[int, int]:
        """Liest einen PID Parameter von allen Servos"""
        with self.lock:
            try:
                self.groupBulkRead.clearParam()
                for dxl_id in self.dxl_ids:
                    success = self.groupBulkRead.addParam(dxl_id, address, LEN_PRO_PID_GAIN)
                    if not success:
                        print(f"[WARN] Konnte ID {dxl_id} nicht registrieren")
                
                result = self.groupBulkRead.txRxPacket()
                if result != COMM_SUCCESS:
                    print(f"[ERROR] BulkRead PID Parameter: {self.packetHandler.getTxRxResult(result)}")
                
                values = {}
                for dxl_id in self.dxl_ids:
                    if self.groupBulkRead.isAvailable(dxl_id, address, LEN_PRO_PID_GAIN):
                        values[dxl_id] = self.groupBulkRead.getData(dxl_id, address, LEN_PRO_PID_GAIN)
                    else:
                        values[dxl_id] = None
                
                self.groupBulkRead.clearParam()
                return values
            except Exception as e:
                print(f"[ERROR] BulkRead PID Parameter error: {e}")
                return {dxl_id: None for dxl_id in self.dxl_ids}

    def bulk_write_pid_parameter(self, address: int, value_dict: Dict[int, int]) -> bool:
        """Schreibt einen PID Parameter für mehrere Servos"""
        with self.lock:
            try:
                self.groupBulkWrite.clearParam()
                for dxl_id, value in value_dict.items():
                    param_data = [DXL_LOBYTE(value), DXL_HIBYTE(value)]
                    success = self.groupBulkWrite.addParam(dxl_id, address, LEN_PRO_PID_GAIN, param_data)
                    if not success:
                        print(f"[WARN] Konnte Parameter für ID {dxl_id} nicht hinzufügen")
                        return False

                result = self.groupBulkWrite.txPacket()
                if result != COMM_SUCCESS:
                    print(f"[ERROR] BulkWrite PID Parameter: {self.packetHandler.getTxRxResult(result)}")
                    return False

                self.groupBulkWrite.clearParam()
                return True
            except Exception as e:
                print(f"[ERROR] BulkWrite PID Parameter error: {e}")
                return False

    # Velocity PID Operations
    def bulk_read_velocity_i_gains(self) -> Dict[int, int]:
        """Liest Velocity I Gain von allen Motoren"""
        return self.bulk_read_pid_parameter(ADDR_PRO_VELOCITY_I_GAIN)

    def bulk_read_velocity_p_gains(self) -> Dict[int, int]:
        """Liest Velocity P Gain von allen Motoren"""
        return self.bulk_read_pid_parameter(ADDR_PRO_VELOCITY_P_GAIN)

    def bulk_write_velocity_i_gains(self, value_dict: Dict[int, int]) -> bool:
        """Schreibt Velocity I Gain für mehrere Motoren"""
        # Validierung
        for dxl_id, value in value_dict.items():
            if not self._validate_velocity_pid('i', value):
                return False
        return self.bulk_write_pid_parameter(ADDR_PRO_VELOCITY_I_GAIN, value_dict)

    def bulk_write_velocity_p_gains(self, value_dict: Dict[int, int]) -> bool:
        """Schreibt Velocity P Gain für mehrere Motoren"""
        # Validierung
        for dxl_id, value in value_dict.items():
            if not self._validate_velocity_pid('p', value):
                return False
        return self.bulk_write_pid_parameter(ADDR_PRO_VELOCITY_P_GAIN, value_dict)

    # Position PID Operations
    def bulk_read_position_p_gains(self) -> Dict[int, int]:
        """Liest Position P Gain von allen Motoren"""
        return self.bulk_read_pid_parameter(ADDR_PRO_POSITION_P_GAIN)

    def bulk_read_position_i_gains(self) -> Dict[int, int]:
        """Liest Position I Gain von allen Motoren"""
        return self.bulk_read_pid_parameter(ADDR_PRO_POSITION_I_GAIN)

    def bulk_read_position_d_gains(self) -> Dict[int, int]:
        """Liest Position D Gain von allen Motoren"""
        return self.bulk_read_pid_parameter(ADDR_PRO_POSITION_D_GAIN)

    def bulk_write_position_p_gains(self, value_dict: Dict[int, int]) -> bool:
        """Schreibt Position P Gain für mehrere Motoren"""
        return self.bulk_write_pid_parameter(ADDR_PRO_POSITION_P_GAIN, value_dict)

    def bulk_write_position_i_gains(self, value_dict: Dict[int, int]) -> bool:
        """Schreibt Position I Gain für mehrere Motoren"""
        return self.bulk_write_pid_parameter(ADDR_PRO_POSITION_I_GAIN, value_dict)

    def bulk_write_position_d_gains(self, value_dict: Dict[int, int]) -> bool:
        """Schreibt Position D Gain für mehrere Motoren"""
        return self.bulk_write_pid_parameter(ADDR_PRO_POSITION_D_GAIN, value_dict)

    # Combined Operations
    def bulk_read_velocity_pid_gains(self) -> Dict[int, Dict[str, int]]:
        """Liest alle Velocity PID Parameter"""
        i_gains = self.bulk_read_velocity_i_gains()
        p_gains = self.bulk_read_velocity_p_gains()
        
        return {
            dxl_id: {
                'i': i_gains.get(dxl_id, 0),
                'p': p_gains.get(dxl_id, 0)
            }
            for dxl_id in self.dxl_ids
        }

    def bulk_read_pid_gains(self) -> Dict[int, Dict[str, int]]:
        """Liest alle PID Parameter (Position und Velocity)"""
        pos_gains = self.bulk_read_position_pid_gains()
        vel_gains = self.bulk_read_velocity_pid_gains()
        
        # Combine position and velocity gains
        combined_gains = {}
        for dxl_id in self.dxl_ids:
            combined_gains[dxl_id] = {
                'p': pos_gains.get(dxl_id, {}).get('p', 0),
                'i': pos_gains.get(dxl_id, {}).get('i', 0),
                'd': pos_gains.get(dxl_id, {}).get('d', 0),
                'vel_p': vel_gains.get(dxl_id, {}).get('p', 0),
                'vel_i': vel_gains.get(dxl_id, {}).get('i', 0)
            }
        return combined_gains

    def bulk_read_position_pid_gains(self) -> Dict[int, Dict[str, int]]:
        """Liest alle Position PID Parameter"""
        p_gains = self.bulk_read_position_p_gains()
        i_gains = self.bulk_read_position_i_gains()
        d_gains = self.bulk_read_position_d_gains()
        
        return {
            dxl_id: {
                'p': p_gains.get(dxl_id, 0),
                'i': i_gains.get(dxl_id, 0),
                'd': d_gains.get(dxl_id, 0)
            }
            for dxl_id in self.dxl_ids
        }

    def bulk_write_velocity_pid_gains(self, pid_dict: Dict[int, Dict[str, int]]) -> bool:
        """Schreibt alle Velocity PID Parameter"""
        i_values = {dxl_id: gains['i'] for dxl_id, gains in pid_dict.items() if 'i' in gains}
        p_values = {dxl_id: gains['p'] for dxl_id, gains in pid_dict.items() if 'p' in gains}
        
        i_success = self.bulk_write_velocity_i_gains(i_values)
        p_success = self.bulk_write_velocity_p_gains(p_values)
        
        return i_success and p_success

    def bulk_write_position_pid_gains(self, pid_dict: Dict[int, Dict[str, int]]) -> bool:
        """Schreibt alle Position PID Parameter"""
        p_values = {dxl_id: gains['p'] for dxl_id, gains in pid_dict.items() if 'p' in gains}
        i_values = {dxl_id: gains['i'] for dxl_id, gains in pid_dict.items() if 'i' in gains}
        d_values = {dxl_id: gains['d'] for dxl_id, gains in pid_dict.items() if 'd' in gains}
        
        p_success = self.bulk_write_position_p_gains(p_values)
        i_success = self.bulk_write_position_i_gains(i_values)
        d_success = self.bulk_write_position_d_gains(d_values)
        
        return p_success and i_success and d_success
