from .j2534_connection import J2534Connection

import can
import struct
import time
import sys
from collections import namedtuple


class CAN_MESSAGE():
    def __init__(self, id, data):
        self.id = id
        if isinstance(data, bytes):
            self.data = bytes(data)
        elif isinstance(data, bytearray):
            self.data = data
        elif isinstance(data, list):
            try:
                self.data = bytes(data)
            except Exception as e:
                raise TypeError(f"List elements must be integers between 0 and 255: {e}")
        else:
            raise TypeError(f"data must be bytes or list of integers, got {type(data).__name__}")

    def __str__(self):
        dlc = len(self.data)
        data_str = ' '.join(f'{b:02X}' for b in self.data)
        return f'{self.id:03X} [{dlc}] {data_str}'


class CANBUS:
    def __init__(self, j2534_device_name=""):
        is_windows = sys.platform.startswith('win')
        if is_windows:
            from connection.j2534_detect import J2534RegistryDetector
            detector = J2534RegistryDetector()
            devices = detector.list_devices_short()
            if devices.get(j2534_device_name):
                dll_name = devices[j2534_device_name]
            else:
                dll_name = list(devices.values())[0]

            self.bus = J2534Connection(dll_name)
            self.bus.open()
            pass
        else:
            self.bus = can.interface.Bus(channel="can0", bustype="socketcan")

        self.debug = False

    def can_send(self, msg: CAN_MESSAGE):
        timeout = 1000
        can_msg = can.Message(
            arbitration_id=msg.id, data=msg.data, is_extended_id=False
        )
        self.bus.send(can_msg, timeout)
        pass

    def can_recv(self, timeout=1) -> CAN_MESSAGE:
        message = self.bus.recv(timeout)
        if message is not None:
            message = CAN_MESSAGE(message.arbitration_id, message.data)
        return message

    def print(self, *args):
        if self.debug:
            print(args)

    def disconnect(self):
        self.bus.close()
        pass
