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

    def bulk_read_positions(self, motor_ids):
        print("[DEBUG] Initializing GroupBulkRead...")
        try:
            group_bulk_read = GroupBulkRead(self.port_handler, self.packet_handler)
            for motor_id in motor_ids:
                group_bulk_read.addParam(motor_id, PRESENT_POSITION, LEN_PRO_PRESENT_POSITION)

            comm_result = group_bulk_read.txRxPacket()
            if comm_result != COMM_SUCCESS:
                raise Exception(f"Bulk read failed with result: {comm_result}")

            positions = {}
            for motor_id in motor_ids:
                position = group_bulk_read.getData(motor_id, PRESENT_POSITION, LEN_PRO_PRESENT_POSITION)
                positions[motor_id] = position

            return positions
        except NameError as e:
            print("[ERROR] GroupBulkRead not properly defined or imported.")
            raise e

    def bulk_read_data(self, motor_ids, data_addresses):
        print("[DEBUG] Performing bulk read for multiple parameters...")
        try:
            group_bulk_read = GroupBulkRead(self.port_handler, self.packet_handler)
            for motor_id in motor_ids:
                for address, length in data_addresses:
                    group_bulk_read.addParam(motor_id, address, length)

            comm_result = group_bulk_read.txRxPacket()
            if comm_result != COMM_SUCCESS:
                raise Exception(f"Bulk read failed with result: {comm_result}")

            data = {}
            for motor_id in motor_ids:
                motor_data = {}
                for address, length in data_addresses:
                    value = group_bulk_read.getData(motor_id, address, length)
                    motor_data[address] = value
                data[motor_id] = motor_data

            return data
        except Exception as e:
            print("[ERROR] Bulk read failed: ", str(e))
            raise e

    def bulk_write_positions(self, target_positions):
        for motor_id, position in target_positions.items():
            param_goal_position = [
                DXL_LOBYTE(DXL_LOWORD(position)),
                DXL_HIBYTE(DXL_LOWORD(position)),
                DXL_LOBYTE(DXL_HIWORD(position)),
                DXL_HIBYTE(DXL_HIWORD(position)),
            ]
            print(f"[DEBUG] Adding Motor ID {motor_id}: Position {position}, Data {param_goal_position}")
            success = self.group_bulk_write.addParam(motor_id, GOAL_POSITION, LEN_PRO_GOAL_POSITION, bytes(param_goal_position))
            if not success:
                raise Exception(f"Failed to add parameter for Motor ID {motor_id}")

        comm_result = self.group_bulk_write.txPacket()
        if comm_result != COMM_SUCCESS:
            raise Exception(f"Bulk write failed with result: {comm_result}")
        print("Bulk write succeeded")
        self.group_bulk_write.clearParam()

    def get_present_position(self, motor_id):
        self.validate_motor_id(motor_id)
        result, comm_result, error = self.packet_handler.read4ByteTxRx(self.port_handler, motor_id, PRESENT_POSITION)
        if comm_result == COMM_SUCCESS and error == 0:
            if result > 0x7FFFFFFF:
                result -= 0x100000000
            return self.convert_to_units(result, motor_id)
        else:
            raise Exception(f"Error reading position: Motor ID {motor_id}, comm_result={comm_result}, error={error}")

    def set_goal_position(self, motor_id, position):
        self.validate_motor_id(motor_id)
        steps = self.convert_to_steps(position, motor_id)
        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, GOAL_POSITION, steps)
        if result != COMM_SUCCESS or error != 0:
            raise Exception(f"Failed to set goal position: Motor ID {motor_id}, result={result}, error={error}")

    def close(self):
        self.port_handler.closePort()

    def get_bulk_motor_data(self, motor_ids):
        data_addresses = [
            (PRESENT_POSITION, LEN_PRO_PRESENT_POSITION),
            (TEMPERATURE_ADDR, LEN_PRO_TEMPERATURE),
            (CURRENT_ADDR, LEN_PRO_CURRENT),
            (VOLTAGE_ADDR, LEN_PRO_VOLTAGE),
            (TORQUE_ADDR, LEN_PRO_TORQUE)
        ]
        raw_data = self.bulk_read_data(motor_ids, data_addresses)
        formatted_data = {}
        for motor_id, values in raw_data.items():
            formatted_data[motor_id] = {
                "position": values[PRESENT_POSITION],
                "temperature": values[TEMPERATURE_ADDR],
                "current": values[CURRENT_ADDR],
                "voltage": values[VOLTAGE_ADDR],
                "torque": values[TORQUE_ADDR]
            }
        return formatted_data
