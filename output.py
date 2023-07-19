import os
import subprocess

SELFDIR = os.path.abspath(f'{__file__}/..')

from src.OPi import OPiTools


if __name__ == '__main__':
    import time
    # create pin classes from PINLIST dict
    pins = [OPiTools.Pin(**pin) for pin in OPiTools.PINLIST]
    # create GPIOmgr class
    GPIO = OPiTools.GPIOmgr(pins)
    # set physical pin 7 to output
    GPIO.setMode(GPIO.phys2wPi(7), OPiTools.OUTPUT)
    # create a blink loop
    while True:
        GPIO.digitalwrite(GPIO.phys2wPi(7), OPiTools.HIGH)
        time.sleep(1)
        GPIO.digitalwrite(GPIO.phys2wPi(7), OPiTools.LOW)
        time.sleep(1)
