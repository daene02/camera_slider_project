import os
import sys
from dynamixel_sdk import PortHandler, PacketHandler, GroupBulkWrite, GroupBulkRead, DXL_LOBYTE, DXL_LOWORD, DXL_HIBYTE, DXL_HIWORD, COMM_SUCCESS
from settings import *
import logging
import time
import asyncio

class MotorController:
    def __init__(self):
        self.port_handler = PortHandler(DEVICENAME)
        self.packet_handler = PacketHandler(PROTOCOL_VERSION)

        print("Initializing port handler...")
        if not self.port_handler.openPort():
            print("[ERROR] Failed to open the port")
            raise IOError("Failed to open port.")
        if not self.port_handler.setBaudRate(BAUDRATE):
            print("[ERROR] Failed to set baud rate")
            raise IOError("Failed to set baudrate.")

        # Initialize GroupBulkWrite
        self.group_bulk_write = GroupBulkWrite(self.port_handler, self.packet_handler)
        print("Initialized GroupBulkWrite")

    def validate_motor_id(self, motor_id):
        if motor_id not in MOTOR_NAMES.keys():
            raise ValueError(f"Invalid motor ID: {motor_id}")

    def validate_mode(self, mode):
        if mode not in range(0, 6):
            raise ValueError(f"Invalid operating mode: {mode}")

    def set_pid_gains(self, motor_id, velocity_i_gain, velocity_p_gain, position_d_gain, position_i_gain, position_p_gain):
        self.validate_motor_id(motor_id)

        print(f"Setze PID-Gains für Motor ID {motor_id}")
        self.packet_handler.write2ByteTxRx(self.port_handler, motor_id, VELOCITY_I_GAIN, velocity_i_gain)
        self.packet_handler.write2ByteTxRx(self.port_handler, motor_id, VELOCITY_P_GAIN, velocity_p_gain)
        self.packet_handler.write2ByteTxRx(self.port_handler, motor_id, POSITION_D_GAIN, position_d_gain)
        self.packet_handler.write2ByteTxRx(self.port_handler, motor_id, POSITION_I_GAIN, position_i_gain)
        self.packet_handler.write2ByteTxRx(self.port_handler, motor_id, POSITION_P_GAIN, position_p_gain)
        print(f"PID-Gains für Motor ID {motor_id} gesetzt: V_I={velocity_i_gain}, V_P={velocity_p_gain}, P_D={position_d_gain}, P_I={position_i_gain}, P_P={position_p_gain}")

    def convert_to_units(self, steps, motor_id):
        factor = CONVERSION_FACTORS.get(MOTOR_NAMES.get(motor_id, None), 1)

        if factor == 1:
            return steps

        units = steps * factor
        return units

    def convert_to_steps(self, value, motor_id):
        self.validate_motor_id(motor_id)
        factor = CONVERSION_FACTORS.get(MOTOR_NAMES.get(motor_id, None), 1)

        if factor == 1 or isinstance(value, int):
            return value

        steps = int(value / factor)
        return steps

    def set_operating_mode(self, motor_id, mode):
        self.validate_motor_id(motor_id)
        self.validate_mode(mode)
        self.disable_torque(motor_id)

        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, OPERATING_MODE, mode)
        if result != COMM_SUCCESS or error != 0:
            raise Exception(f"Fehler beim Setzen des Betriebsmodus: Motor ID {motor_id}, Ergebnis {result}, Fehler {error}")

        self.enable_torque(motor_id)

    def enable_torque(self, motor_id):
        self.validate_motor_id(motor_id)
        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, TORQUE_ENABLE, 1)
        if result != COMM_SUCCESS or error != 0:
            raise Exception(f"Failed to enable torque: Motor ID {motor_id}, result={result}, error={error}")

    def disable_torque(self, motor_id):
        self.validate_motor_id(motor_id)
        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, TORQUE_ENABLE, 0)
        if result != COMM_SUCCESS or error != 0:
            raise Exception(f"Failed to disable torque: Motor ID {motor_id}, result={result}, error={error}")
 
    def shutdown_system(self):
        """
        Shutdown-System via API.
        """
        try:
            os.system("sudo shutdown -h now")
            print("[INFO] Das System wird heruntergefahren.")
        except Exception as e:
            print(f"[ERROR] Fehler beim Herunterfahren des Systems: {e}")
 
    def close(self):
        self.port_handler.closePort()


