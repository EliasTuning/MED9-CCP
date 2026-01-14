import winreg


class PassThruDeviceInfo:
    def __init__(self, name, values):
        self.name = name
        self.values = values
        # Explicit properties
        self.Name = values.get('Name')
        self.Vendor = values.get('Vendor')
        self.ConfigApplication = values.get('ConfigApplication')
        self.DeviceId = values.get('DeviceId', 0)
        self.CAN = values.get('CAN', 0)
        self.ISO9141 = values.get('ISO9141', 0)
        self.ISO9141_CH1 = values.get('ISO9141_CH1', 0)
        self.ISO9141_CH2 = values.get('ISO9141_CH2', 0)
        self.ISO9141_CH3 = values.get('ISO9141_CH3', 0)
        self.ISO14230 = values.get('ISO14230', 0)
        self.ISO14230_CH1 = values.get('ISO14230_CH1', 0)
        self.ISO14230_CH2 = values.get('ISO14230_CH2', 0)
        self.ISO14230_CH3 = values.get('ISO14230_CH3', 0)
        self.ISO15765 = values.get('ISO15765', 0)
        self.J1850PWM = values.get('J1850PWM', 0)
        self.J1850VPW = values.get('J1850VPW', 0)
        self.FunctionLibrary = values.get('FunctionLibrary')

    def __repr__(self):
        return (
            f"<PassThruDeviceInfo name={self.name!r}, Name={self.Name!r}, Vendor={self.Vendor!r}, "
            f"ConfigApplication={self.ConfigApplication!r}, DeviceId={self.DeviceId!r}, CAN={self.CAN!r}, "
            f"ISO9141={self.ISO9141!r}, ISO9141_CH1={self.ISO9141_CH1!r}, ISO9141_CH2={self.ISO9141_CH2!r}, "
            f"ISO9141_CH3={self.ISO9141_CH3!r}, ISO14230={self.ISO14230!r}, ISO14230_CH1={self.ISO14230_CH1!r}, "
            f"ISO14230_CH2={self.ISO14230_CH2!r}, ISO14230_CH3={self.ISO14230_CH3!r}, ISO15765={self.ISO15765!r}, "
            f"J1850PWM={self.J1850PWM!r}, J1850VPW={self.J1850VPW!r}, FunctionLibrary={self.FunctionLibrary!r}, "
            f"values={self.values!r}>")


class J2534RegistryDetector:
    REG_PATH = r"SOFTWARE\\Wow6432Node\\PassThruSupport.04.04"

    def list_devices(self):
        devices = []
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.REG_PATH) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey_path = f"{self.REG_PATH}\\{subkey_name}"
                        values = self._read_subkey_values(subkey_path)
                        devices.append(PassThruDeviceInfo(subkey_name, values))
                        i += 1
                    except OSError:
                        break  # No more subkeys
        except FileNotFoundError:
            pass  # Registry path does not exist
        return devices

    def _read_subkey_values(self, subkey_path):
        values = {}
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                j = 0
                while True:
                    try:
                        value = winreg.EnumValue(subkey, j)
                        values[value[0]] = value[1]
                        j += 1
                    except OSError:
                        break  # No more values
        except FileNotFoundError:
            pass  # Subkey does not exist
        return values

    def list_devices_short(self):
        devices = self.list_devices()
        retList = {}
        for device in devices:
            retList[device.name] = device.FunctionLibrary
        return retList
