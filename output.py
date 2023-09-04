import os
import time
import threading

SELFDIR = os.path.abspath(f'{__file__}/..')

from src.OPi import OPiTools

# time in seconds
TRIGGER_TIME = 3
TRIGGER_ENTRY_DELAY = 2
TRIGGER_EXIT_DELAY = 2

ENTER_EVENT = 0
TRIGGER_ENTER_EVENT = 1
TRIGGER_EXIT_EVENT = 2
EXIT_EVENT = 3


class Outputmgr:
    # unused
    state_translate = {
        'idle': 'enter',
        'enter': 'trigger',
        'trigger': 'exit',
        'exit': 'idle'
    }

    def __init__(self):
        self.events = []
        self.state = 'idle'
        self.laststate = 'idle'
        self.last_state_change = time.time()
        self.next_state_change = 0
        self.interrupt = False

    def trigger(self):
        self.laststate = self.state
        self.state = 'enter'
        if self.laststate == 'enter':
            pass
        elif self.laststate == 'idle':
            self.next_state_change = time.time() + TRIGGER_ENTRY_DELAY
        elif self.laststate == 'trigger':
            self.next_state_change = time.time() + TRIGGER_TIME
            self.state = 'trigger'
        elif self.laststate == 'exit':
            self.next_state_change = time.time() + (time.time() - self.last_state_change)
        self.last_state_change = time.time()

    def check_loop(self):
        while not self.interrupt:
            if self.state != self.laststate:
                print(f"State changed from {self.laststate} to {self.state}")
                if self.state == 'enter':
                    self.main_enter()
                elif self.state == 'trigger':
                    self.main_trigger()
                elif self.state == 'exit':
                    self.main_exit()
                elif self.state == 'idle':
                    self.main_idle()
            if self.next_state_change <= time.time() and self.next_state_change != 0:
                self.laststate = self.state
                self.state = self.state_translate[self.state]

    def main_enter(self):
        if self.laststate == 'idle':
            self.next_state_change = time.time() + TRIGGER_ENTRY_DELAY
            for event in self.events:
                if event['type'] == ENTER_EVENT:
                    event['callback']()
        elif self.laststate == 'exit' or self.laststate == 'enter':
            self.next_state_change = time.time() + (time.time() - self.last_state_change)
            for event in self.events:
                if event['type'] == ENTER_EVENT:
                    event['callback']()
        self.laststate = self.state
        self.last_state_change = time.time()

    def main_trigger(self):
        self.next_state_change = time.time() + TRIGGER_TIME
        for event in self.events:
            if event['type'] == TRIGGER_ENTER_EVENT:
                event['callback']()
        self.laststate = self.state
        self.last_state_change = time.time()

    def main_exit(self):
        self.next_state_change = time.time() + TRIGGER_EXIT_DELAY
        for event in self.events:
            if event['type'] == TRIGGER_EXIT_EVENT:
                event['callback']()
        self.laststate = self.state
        self.last_state_change = time.time()

    def main_idle(self):
        self.next_state_change = 0
        for event in self.events:
            if event['type'] == EXIT_EVENT:
                event['callback']()
        self.laststate = self.state
        self.last_state_change = time.time()

    def addeventlistener(self, event, callback):
        self.events.append({'type': event, 'callback': callback})

class Outputhelper:
    # temp pin definitions
    RED = 3
    YELLOW = 5
    GREEN = 7
    GATE_PULSE = 8

    INTERRUPT = 10
    def __init__(self, gpio:OPiTools.GPIOmgr) -> None:
        self.gpio = gpio
        self.allowed_trigger = True

        # setup gpio
        gpio.setMode(gpio.phys2wPi(self.INTERRUPT), OPiTools.INPUT_PULLUP)
        gpio.attachinterrupt(0, gpio.phys2wPi(self.INTERRUPT), self.trigger_enter, OPiTools.RISING)
        gpio.attachinterrupt(1, gpio.phys2wPi(self.INTERRUPT), self.exit, OPiTools.FALLING)

        gpio.setMode(gpio.phys2wPi(self.RED), OPiTools.OUTPUT)
        gpio.setMode(gpio.phys2wPi(self.YELLOW), OPiTools.OUTPUT)
        gpio.setMode(gpio.phys2wPi(self.GREEN), OPiTools.OUTPUT)

        # set default state
        gpio.digitalwrite(gpio.phys2wPi(self.RED), OPiTools.HIGH)
        gpio.digitalwrite(gpio.phys2wPi(self.YELLOW), OPiTools.LOW)
        gpio.digitalwrite(gpio.phys2wPi(self.GREEN), OPiTools.LOW)

    def enter(self):
        if not self.allowed_trigger:
            return
        # detection of lp, start opening gate
        # red low, yellow high, green low
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.RED), OPiTools.LOW)
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.YELLOW), OPiTools.HIGH)
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.GREEN), OPiTools.LOW)
        self.gate_open()

    def trigger_enter(self):
        # gate open, green high, yellow low, red low
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.RED), OPiTools.LOW)
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.YELLOW), OPiTools.LOW)
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.GREEN), OPiTools.HIGH)

    def trigger_exit(self):
        # gate closing, red low, yellow high, green low
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.RED), OPiTools.LOW)
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.YELLOW), OPiTools.HIGH)
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.GREEN), OPiTools.LOW)

    def exit(self):
        # gate closed, red high, yellow low, green low
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.RED), OPiTools.HIGH)
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.YELLOW), OPiTools.LOW)
        self.gpio.digitalwrite(self.gpio.phys2wPi(self.GREEN), OPiTools.LOW)

    def gate_open(self):
        if self.allowed_trigger:
            self.allowed_trigger = False
            self.gpio.digitalwrite(self.gpio.phys2wPi(self.GATE_PULSE), OPiTools.HIGH)
            time.sleep(1)
            self.gpio.digitalwrite(self.gpio.phys2wPi(self.GATE_PULSE), OPiTools.LOW)

    def gate_close(self):
        self.allowed_trigger = True



if __name__ == '__main__':
    import multiprocessing as mp

    out = Outputmgr()
    #gpio = OPiTools.GPIOmgr(OPiTools.PINLIST)
    #outhelper = Outputhelper(out, gpio)

    print("starting check loop")
    # test the output manager
    # add some events
    out.addeventlistener(ENTER_EVENT, lambda: print("enter"))
    out.addeventlistener(TRIGGER_ENTER_EVENT, lambda: print("trigger enter"))
    out.addeventlistener(TRIGGER_EXIT_EVENT, lambda: print("trigger exit"))
    out.addeventlistener(EXIT_EVENT, lambda: print("exit"))

    # start the check loop
    thread = threading.Thread(target=out.check_loop)
    thread.start()
    # trigger the output manager

    out.trigger()
    time.sleep(5)
    out.trigger()
    while True:
        time.sleep(1)

    exit(0)
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
