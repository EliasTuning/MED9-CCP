# CCP (CAN Calibration Protocol) Example
# Usage example for the ccp_lib library

from config import env_float, env_int, open_can
from ccp_lib import CCP


def main():
    bus = open_can()

    ccp = CCP(
        can=bus,
        tx=env_int("CCP_TX", 0x7C3),
        rx=env_int("CCP_RX", 0x7C4),
        timeout=env_float("CCP_TIMEOUT", 1.0),
    )
    print(f"CCP timeout: {ccp.timeout} seconds")

    ccp.connect(station_address=env_int("CCP_STATION_ADDRESS", 0x12ED))

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
