"""Scan standard CAN IDs with a CCP CONNECT and stop on the first unexpected frame."""

import time

from config import env_float, env_id_set, env_int, env_str, open_can
from master import Master


def main():
    dll = env_str("J2534_DLL")
    station = env_int("CCP_STATION_ADDRESS", 0x12ED)
    id_max = env_int("IDENT_ID_MAX", 0x7FF)
    listen_s = env_float("IDENT_LISTEN_S", 0.05)
    ignore = env_id_set("IGNORE_CAN_IDS")

    print(f"DLL: {dll}")
    print(f"CAN speed: {env_int('CAN_SPEED', 500)} kbit/s")
    print(f"Station address: 0x{station:04X}")
    print(f"Scanning CAN IDs 0x000 .. 0x{id_max:03X}, listen {listen_s}s")
    if ignore:
        shown = ", ".join(f"0x{i:03X}" for i in sorted(ignore))
        print(f"Ignoring: {shown}")
    else:
        print("IGNORE_CAN_IDS is empty; any frame other than the request echo stops the scan")

    bus = open_can()
    master = Master()
    try:
        for can_id in range(0, id_max + 1):
            bus.can_send(master.connect(can_id, station))
            deadline = time.monotonic() + listen_s
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                message = bus.can_recv(timeout=remaining)
                if message is None:
                    break
                if message.id == can_id or message.id in ignore:
                    continue
                print(f"CONNECT on 0x{can_id:03X} -> {message}")
                return
            if can_id % 0x40 == 0:
                print(f"... 0x{can_id:03X}")
        print("No unexpected CAN frame seen")
    finally:
        bus.disconnect()


if __name__ == "__main__":
    main()
