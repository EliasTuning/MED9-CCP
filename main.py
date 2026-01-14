# CCP (CAN Calibration Protocol) Example
# Usage example for the ccp_lib library

from connection import canbus
from ccp_lib import CCP


def main():
    # Initialize CAN bus
    bus = canbus.CANBUS()

    # Create CCP instance with TX and RX CAN IDs
    # Timeout can be set in constructor (default: 1.0 seconds)
    # MED91
    #ccp = CCP(can=bus, tx=0x7C3, rx=0x7C4)
    # MED92
    ccp = CCP(can=bus, tx=0x7BC, rx=0x7BD, timeout=2.0)
    
    # Or configure timeout after creation
    # ccp.timeout = 5.0  # Set to 5 seconds
    print(f"CCP timeout: {ccp.timeout} seconds")

    # Connect to ECU with station address
    ccp.connect(station_address=0x12ED)

    # Read memory from address 0x0 (default 4 bytes)
    data = ccp.read_memory(0x7FC76C, 0x1)
    print(f"Memory at 0x0: {data.hex()}")

    # Read more bytes at a specific address
    # data = ccp.read_memory(0x1000, size=16)
    # print(f"Memory at 0x1000: {data.hex()}")

    # Disconnect when done
    ccp.disconnect()
    bus.disconnect()


if __name__ == '__main__':
    main()
