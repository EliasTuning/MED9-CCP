# This is a sample Python script.

# Press Alt+Umschalt+X to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
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
        print(message)
        a = message.id
        dat = message.data



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
