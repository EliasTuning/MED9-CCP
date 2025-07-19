# This is a sample Python script.

# Press Alt+Umschalt+X to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import time

from connection import canbus
from master import Master


def print_hi(name):
    master = Master()
    bus = canbus.CANBUS()
    bus.can_send(master.connect(0x7C3, 0x12ED))
    while 1:
        message = bus.can_recv()
        if message is None:
            continue
        ign_can_ids = [0x280, 0x540, 0x380, 0x488, 0x284, 0x48A, 0x58C, 0x288, 0x48C, 0x480, 0x588, 0x580]
        if message.id in ign_can_ids:
            continue
        print(message)

        # time.sleep(1)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
