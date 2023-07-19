import subprocess

HIGH = 1
LOW = 0

OUTPUT = 0
INPUT = 1
INPUT_PULLUP = 2

PINLIST = [
    {'name': '3.3V', 'Physical': 1, 'wPi': -1, 'GPIO': -1, 'pinmode': None},            {'name': '5V', 'Physical': 2, 'wPi': -1, 'GPIO': -1, 'pinmode': None},
    {'name': 'SDA.5', 'Physical': 3, 'wPi': 0, 'GPIO': 47, 'pinmode': INPUT},           {'name': '5V', 'Physical': 4, 'wPi': -1, 'GPIO': -1, 'pinmode': None},
    {'name': 'SCL.5', 'Physical': 5, 'wPi': 1, 'GPIO': 46, 'pinmode': INPUT},           {'name': 'GND', 'Physical': 6, 'wPi': -1, 'GPIO': -1, 'pinmode': None},
    {'name': 'PWM15', 'Physical': 7, 'wPi': 2, 'GPIO': 54, 'pinmode': INPUT},           {'name': 'RXD.0', 'Physical': 8, 'wPi': 3, 'GPIO': 131, 'pinmode': INPUT},
    {'name': 'GND', 'Physical': 9, 'wPi': -1, 'GPIO': -1, 'pinmode': None},             {'name': 'TXD.0', 'Physical': 10, 'wPi': 4, 'GPIO': 132, 'pinmode': INPUT},
    {'name': 'CAN1_RX', 'Physical': 11, 'wPi': 5, 'GPIO': 138, 'pinmode': INPUT},       {'name': 'CAN2_TX', 'Physical': 12, 'wPi': 6, 'GPIO': 29, 'pinmode': INPUT},
    {'name': 'CAN1_TX', 'Physical': 13, 'wPi': 7, 'GPIO': 139, 'pinmode': INPUT},       {'name': 'GND', 'Physical': 14, 'wPi': -1, 'GPIO': -1, 'pinmode': None},
    {'name': 'CAN2_RX', 'Physical': 15, 'wPi': 8, 'GPIO': 28, 'pinmode': INPUT},        {'name': 'SDA.1', 'Physical': 16, 'wPi': 9, 'GPIO': 59, 'pinmode': INPUT},
    {'name': '3.3V', 'Physical': 17, 'wPi': -1, 'GPIO': -1, 'pinmode': None},           {'name': 'SCL.1', 'Physical': 18, 'wPi': 10, 'GPIO': 58, 'pinmode': INPUT},
    {'name': 'SPI4_TXD', 'Physical': 19, 'wPi': 11, 'GPIO': 49, 'pinmode': INPUT},      {'name': 'GND', 'Physical': 20, 'wPi': -1, 'GPIO': -1, 'pinmode': None},
    {'name': 'SPI4_RXD', 'Physical': 21, 'wPi': 12, 'GPIO': 48, 'pinmode': INPUT},      {'name': 'PowerKey', 'Physical': 22, 'wPi': -1, 'GPIO': -1, 'pinmode': None},
    {'name': 'SPI4_CLK', 'Physical': 23, 'wPi': 13, 'GPIO': 50, 'pinmode': INPUT},      {'name': 'SPI4_CS1', 'Physical': 24, 'wPi': 14, 'GPIO': 52, 'pinmode': INPUT},
    {'name': 'GND', 'Physical': 25, 'wPi': -1, 'GPIO': -1, 'pinmode': None},            {'name': 'PWM1', 'Physical': 26, 'wPi': 15, 'GPIO': 35, 'pinmode': INPUT},
]

class Pin:
    defaut_pin_info = {
        'GPIO': -1,
        'wPi': -1,
        'Physical': -1,
        'name': '',
        'pinmode': None
    }

    mode_translate = {
        OUTPUT: 'OUTPUT',
        INPUT: 'INPUT',
        INPUT_PULLUP: 'INPUT_PULLUP'
    }
    def __init__(self, **pin_info) -> None:
        # set default values
        for key, value in Pin.defaut_pin_info.items():
            if key not in pin_info:
                pin_info[key] = value
        self.GPIO = pin_info['GPIO']
        self.wPi = pin_info['wPi']
        self.physical = pin_info['Physical']
        self.name = pin_info['name']
        self.pinmode = pin_info['pinmode']
        if self.wPi == -1:
            self.value = -1
        else:
            self.value = self.read()


    def write(self, value:int):
        if self.wPi == -1:
            raise ValueError('Cannot write to pin without wPi')
        self.value = value
        subprocess.Popen(['gpio', 'write', str(self.wPi), str(value)])

    def read(self):
        if self.wPi == -1:
            raise ValueError('Cannot read from pin without wPi')
        self.value = int(subprocess.check_output(['gpio', 'read', str(self.wPi)]))
        return self.value

    def mode(self, mode:int):
        if self.wPi == -1:
            raise ValueError('Cannot set mode to pin without wPi')
        if self.mode_translate[mode] == 'INPUT_PULLUP':
            subprocess.Popen(['gpio', 'mode', str(self.wPi), 'INPUT'])
            subprocess.Popen(['gpio', 'mode', str(self.wPi), 'UP'])
            return
        elif self.mode_translate[mode] == 'INPUT':
            subprocess.Popen(['gpio', 'mode', str(self.wPi), 'DOWN'])
        subprocess.Popen(['gpio', 'mode', str(self.wPi), Pin.mode_translate[mode]])

class GPIOmgr:
    def __init__(self, pins:list) -> None:
        self.pins = pins
        self.pinmap_physical = {pin.physical: pin for pin in pins}
        self.pinmap_wPi = {pin.wPi: pin for pin in pins if pin.wPi != -1}
        self.pinmap_GPIO = {pin.GPIO: pin for pin in pins if pin.GPIO != -1}

    def digitalwrite(self, pin_wPi:int, value:int):
        self.pinmap_wPi[pin_wPi].write(value)

    def digitalread(self, pin_wPi:int):
        return self.pinmap_wPi[pin_wPi].read()

    def phys2wPi(self, pin_physical:int):
        return self.pinmap_physical[pin_physical].wPi

    def phys2GPIO(self, pin_physical:int):
        return self.pinmap_physical[pin_physical].GPIO

    def wPi2phys(self, pin_wPi:int):
        return self.pinmap_wPi[pin_wPi].physical

    def wPi2GPIO(self, pin_wPi:int):
        return self.pinmap_wPi[pin_wPi].GPIO

    def GPIO2phys(self, pin_GPIO:int):
        return self.pinmap_GPIO[pin_GPIO].physical

    def GPIO2wPi(self, pin_GPIO:int):
        return self.pinmap_GPIO[pin_GPIO].wPi

    def isWriteable(self, pin_wPi:int):
        output_pins = filter(lambda pin: pin.pinmode == OUTPUT, self.pins)
        return pin_wPi in map(lambda pin: pin.wPi, output_pins)

    def isReadable(self, pin_wPi:int):
        # input pins are readable
        input_pins = filter(lambda pin: pin.pinmode == INPUT or pin.pinmode == INPUT_PULLUP, self.pins)
        return pin_wPi in map(lambda pin: pin.wPi, input_pins)

    def setMode(self, pin_wPi:int, mode:int):
        self.pinmap_wPi[pin_wPi].mode(mode)