# This is a sample Python script.

# Press Alt+Umschalt+X to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from config import open_can


def print_hi(name):
    bus = open_can()
    while 1:
        #bus.can_send(CAN_MESSAGE(0x613, [0x0]))
        message = bus.can_recv()
        if message is None:
            continue
        # ign_can_ids = [0x280, 0x540, 0x380, 0x488, 0x284, 0x48A, 0x58C, 0x288, 0x48C, 0x480, 0x588, 0x580]
        # if message.id in ign_can_ids:
        #    continue
        print(message)

        # time.sleep(1)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
