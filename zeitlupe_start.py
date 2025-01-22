import os
import sys
from dynamixel_sdk import PortHandler, PacketHandler, GroupBulkWrite, DXL_LOBYTE, DXL_LOWORD, DXL_HIBYTE, DXL_HIWORD, COMM_SUCCESS

# Dynamixel Settings
DEVICE_NAME = '/dev/ttyUSB0'  # Change to your port
BAUDRATE = 1000000
PROTOCOL_VERSION = 2.0  # Protocol version 2.0
DXL_IDS = [1, 2, 3, 4]  # Example motor IDs
ADDR_GOAL_POSITION = 116  # Control table address for goal position
ADDR_PRESENT_POSITION = 132  # Control table address for present position
LEN_PRO_GOAL_POSITION = 4  # Length of goal position data
LEN_PRO_PRESENT_POSITION = 4  # Length of present position data

# Initialize PortHandler and PacketHandler
port_handler = PortHandler(DEVICE_NAME)
packet_handler = PacketHandler(PROTOCOL_VERSION)

print("Initializing port handler...")
if not port_handler.openPort():
    print("[ERROR] Failed to open the port")
    sys.exit()
if not port_handler.setBaudRate(BAUDRATE):
    print("[ERROR] Failed to set baud rate")
    sys.exit()

# Initialize GroupBulkWrite
group_bulk_write = GroupBulkWrite(port_handler, packet_handler)
print("Initialized GroupBulkWrite")

# Test data for motors
test_positions = {
    1: 512,  # Midpoint for 10-bit resolution (0-1023)
    2: 256,  # Example position
    3: 768,  # Example position
    4: 1023  # Maximum position for 10-bit resolution
}

# Add parameters for each motor
for motor_id, position in test_positions.items():
    print(f"Processing Motor ID {motor_id} with position {position}")
    param_goal_position = [
        DXL_LOBYTE(DXL_LOWORD(position)),
        DXL_HIBYTE(DXL_LOWORD(position)),
        DXL_LOBYTE(DXL_HIWORD(position)),
        DXL_HIBYTE(DXL_HIWORD(position)),
    ]
    print(f"Prepared param_goal_position: {param_goal_position}")
    try:
        # Correct usage of addParam with explicit data length
        success = group_bulk_write.addParam(motor_id, ADDR_GOAL_POSITION, LEN_PRO_GOAL_POSITION, bytes(param_goal_position))
        if not success:
            print(f"[ERROR] Failed to add parameter for Motor ID {motor_id}")
    except Exception as e:
        print(f"[EXCEPTION] Exception occurred for Motor ID {motor_id}: {e}")

# Transmit bulk write
print("Transmitting bulk write...")
try:
    result = group_bulk_write.txPacket()
    if result != COMM_SUCCESS:
        print(f"[ERROR] Bulk write failed: {packet_handler.getTxRxResult(result)}")
    else:
        print("Bulk write succeeded")
except Exception as e:
    print(f"[EXCEPTION] Exception occurred during bulk write: {e}")

# Clear bulk write parameter storage
group_bulk_write.clearParam()
print("Cleared GroupBulkWrite parameters")

# Close port
port_handler.closePort()
print("Closed port handler")
