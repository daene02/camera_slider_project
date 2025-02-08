"""Bewegungssteuerung für Dynamixel Servos"""

from dynamixel_sdk import (
    DXL_LOBYTE,
    DXL_HIBYTE,
    DXL_LOWORD,
    DXL_HIWORD,
    COMM_SUCCESS,
    GroupBulkRead,
    GroupBulkWrite
)
from .constants import *
from .base_manager import DynamixelBaseManager

class DynamixelMotionManager(DynamixelBaseManager):
    def bulk_write_goal_positions(self, goal_dict):
        """
        Schreibt Ziel-Positionen für mehrere Servos.
        goal_dict = {dxl_id: goal_position}
        """
        with self.lock:
            try:
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

                result = self.groupBulkWrite.txPacket()
                if result != COMM_SUCCESS:
                    print(f"[ERROR] BulkWrite GoalPositions: {self.packetHandler.getTxRxResult(result)}")
                self.groupBulkWrite.clearParam()
                return True
            except Exception as e:
                print(f"[ERROR] BulkWrite GoalPositions error: {e}")
                return False

    def bulk_read_positions(self):
        """Liest die aktuellen Positionen aller Servos"""
        with self.lock:
            self.groupBulkRead.clearParam()
            for dxl_id in self.dxl_ids:
                success = self.groupBulkRead.addParam(dxl_id, ADDR_PRO_PRESENT_POSITION, LEN_PRO_PRESENT_POSITION)
                if not success:
                    print(f"[WARN] Konnte ID {dxl_id} nicht für Present Position registrieren.")

            result = self.groupBulkRead.txRxPacket()
            if result != COMM_SUCCESS:
                print(f"[ERROR] BulkRead Positions: {self.packetHandler.getTxRxResult(result)}")

            positions = {}
            for dxl_id in self.dxl_ids:
                if self.groupBulkRead.isAvailable(dxl_id, ADDR_PRO_PRESENT_POSITION, LEN_PRO_PRESENT_POSITION):
                    data = self.groupBulkRead.getData(dxl_id, ADDR_PRO_PRESENT_POSITION, LEN_PRO_PRESENT_POSITION)
                    positions[dxl_id] = data
                else:
                    positions[dxl_id] = None
            return positions

    def bulk_write_profile_velocity(self, veloc_dict):
        """Schreibt Geschwindigkeitsprofile für mehrere Servos"""
        with self.lock:
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

    def bulk_write_profile_acceleration(self, accel_dict):
        """Schreibt Beschleunigungsprofile für mehrere Servos"""
        with self.lock:
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

    def bulk_read_profile_velocity(self):
        """Liest die Geschwindigkeitsprofile aller Servos"""
        with self.lock:
            try:
                # Wiederverwendung der bestehenden GroupBulkRead-Instanz
                self.groupBulkRead.clearParam()
                for dxl_id in self.dxl_ids:
                    ok = self.groupBulkRead.addParam(dxl_id, ADDR_PRO_PROFILE_VELOC, LEN_PRO_PROFILE_PARAM)
                    if not ok:
                        print(f"[WARN] Konnte ID {dxl_id} nicht für Profile Velocity registrieren.")

                result = self.groupBulkRead.txRxPacket()
                if result != COMM_SUCCESS:
                    print(f"[ERROR] BulkRead Profile Velocity: {self.packetHandler.getTxRxResult(result)}")

                velocities = {}
                for dxl_id in self.dxl_ids:
                    if self.groupBulkRead.isAvailable(dxl_id, ADDR_PRO_PROFILE_VELOC, LEN_PRO_PROFILE_PARAM):
                        velocities[dxl_id] = self.groupBulkRead.getData(dxl_id, ADDR_PRO_PROFILE_VELOC, LEN_PRO_PROFILE_PARAM)
                    else:
                        velocities[dxl_id] = None

                self.groupBulkRead.clearParam()
                return velocities
            except Exception as e:
                print(f"[ERROR] BulkRead Profile Velocity error: {e}")
                return {}

    def bulk_read_profile_acceleration(self):
        """Liest die Beschleunigungsprofile aller Servos"""
        with self.lock:
            try:
                # Wiederverwendung der bestehenden GroupBulkRead-Instanz
                self.groupBulkRead.clearParam()
                for dxl_id in self.dxl_ids:
                    ok = self.groupBulkRead.addParam(dxl_id, ADDR_PRO_PROFILE_ACCEL, LEN_PRO_PROFILE_PARAM)
                    if not ok:
                        print(f"[WARN] Konnte ID {dxl_id} nicht für Profile Acceleration registrieren.")

                result = self.groupBulkRead.txRxPacket()
                if result != COMM_SUCCESS:
                    print(f"[ERROR] BulkRead Profile Acceleration: {self.packetHandler.getTxRxResult(result)}")

                accels = {}
                for dxl_id in self.dxl_ids:
                    if self.groupBulkRead.isAvailable(dxl_id, ADDR_PRO_PROFILE_ACCEL, LEN_PRO_PROFILE_PARAM):
                        accels[dxl_id] = self.groupBulkRead.getData(dxl_id, ADDR_PRO_PROFILE_ACCEL, LEN_PRO_PROFILE_PARAM)
                    else:
                        accels[dxl_id] = None

                self.groupBulkRead.clearParam()
                return accels
            except Exception as e:
                print(f"[ERROR] BulkRead Profile Acceleration error: {e}")
                return {}
