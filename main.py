# This is a sample Python script.

# Press Alt+Umschalt+X to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from connection import canbus
from master import Master


def print_hi(name):
    master = Master()
    print(master.connect(0x7C3, 0x12ED))
    # bus = canbus.CANBUS()
    # bus.can_send()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
