import os
import subprocess

SELFDIR = os.path.abspath(f'{__file__}/..')

from src.OPi import OPiTools

class Pin:
    defaut_pin_info = {
        'GPIO': -1,
        'wPi': -1,
        'Physical': -1,
        'name': '',
        'pinmode': None
    }
    def __init__(self, **pin_info) -> None:
        pin_info = {**self.defaut_pin_info, **pin_info}
        self.GPIO = pin_info['GPIO']
        self.wPi = pin_info['wPi']
        self.physical = pin_info['Physical']
        self.name = pin_info['name']
        self.pinmode = pin_info['pinmode']
        if self.wPi == -1:
            self.value = self.read()
        else:
            self.value = -1


    def write(self, value:int):
        if self.wPi == -1:
            raise ValueError('Cannot write to pin without wPi')
        self.value = value
        subprocess.Popen(['gpio', 'write', self.wPi, value])

    def read(self):
        if self.wPi == -1:
            raise ValueError('Cannot read from pin without wPi')
        self.value = int(subprocess.check_output(['gpio', 'read', self.wPi]))
        return self.value

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
        output_pins = filter(lambda pin: pin.pinmode == OPiTools.OUTPUT, self.pins)
        return pin_wPi in map(lambda pin: pin.wPi, output_pins)

    def isReadable(self, pin_wPi:int):
        # input pins are readable
        input_pins = filter(lambda pin: pin.pinmode == OPiTools.INPUT or pin.pinmode == OPiTools.INPUT_PULLUP, self.pins)
        return pin_wPi in map(lambda pin: pin.wPi, input_pins)

    def setMode(self, pin_wPi:int, mode:int):
        if mode == OPiTools.OUTPUT:
            self.pinmap_wPi[pin_wPi].pinmode = OPiTools.OUTPUT
        elif mode == OPiTools.INPUT:
            self.pinmap_wPi[pin_wPi].pinmode = OPiTools.INPUT
        elif mode == OPiTools.INPUT_PULLUP:
            self.pinmap_wPi[pin_wPi].pinmode = OPiTools.INPUT_PULLUP
        else:
            raise ValueError(f'Invalid mode {mode}')


if __name__ == '__main__':
    import time
    # create pin classes from PINLIST dict
    pins = [Pin(**pin) for pin in OPiTools.PINLIST]
    # create GPIOmgr class
    GPIO = GPIOmgr(pins)
    # set physical pin 7 to output
    GPIO.setMode(GPIO.phys2wPi(7), OPiTools.OUTPUT)
    # create a blink loop
    while True:
        GPIO.digitalwrite(GPIO.phys2wPi(7), OPiTools.HIGH)
        time.sleep(1)
        GPIO.digitalwrite(GPIO.phys2wPi(7), OPiTools.LOW)
        time.sleep(1)
