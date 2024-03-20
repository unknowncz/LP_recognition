import argparse
import logging
import os
from configparser import ConfigParser
from time import sleep
import threading

from . import SELFDIR

parser = argparse.ArgumentParser(description="""License Plate Recognition Tools""")
parser.add_argument("-l", "--log", type=str, default=f"{SELFDIR}/log", help="Path to the log file")
parser.add_argument("-d", "--desktop", action="store_true", help="Disable GPIO control. This option is useful for desktop environments where GPIO is not present. Default is False.")
parser.add_argument("-c", "--config", type=str, default=os.path.join(SELFDIR, "config.ini"), help="Path to the configuration file. Default is config.ini in the module directory.")
parser.add_argument("--ui-type", type=str.lower, choices=["qt", "web", "none"], default="qt", help="""
                    Type of UI to use, 'qt' (default) - a PyQt5-based UI will be used.\r\n
                    'web' - Web UI will be used.\r\n
                    'none' - No UI will be used. Only for logging purposes.""")
args = parser.parse_args()

if hasattr(args, "help"):
    parser.print_help()
    exit(0)

from . import manager, output, logger


trigger_allowed = True
def unblock(f):
    global trigger_allowed
    if not trigger_allowed:
        return
    def wait_for(f):
        global trigger_allowed
        f()
        trigger_allowed = True
    trigger_allowed = False
    threading.Thread(target=wait_for, args=(f,), daemon=True).start()

def main():
    if not os.path.exists(os.path.dirname(args.log)) or os.access(args.log, os.W_OK):
        manager.logger.error("Provided log filepath is invalid or read-only. Defaulting to module directory")
        args.log = os.path.join(SELFDIR, "log")
    manager.logger.addHandler(logging.FileHandler(os.path.abspath(args.log), mode='w'))

    if args.desktop:
        manager.logger.info("Desktop mode enabled. GPIO control is disabled.")

    if getattr(args, "ui_type") == "web":
        manager.logger.warn("Web-based UI not yet implemented. Defaulting to Qt UI")
        #setattr(args, "ui_type", "qt")

    try:
        flag = ["qt", "web", "none"].index(args.ui_type)
    except ValueError:
        flag = manager.flags.Flag.FLAG_GUI_QT
    manager.flags.set_flag(manager.flags.Types.TYPE_GUI, flag)

    config = ConfigParser()
    config.read(args.config)
    manager.config = config
    if not args.desktop:
        pins = [output.OPiTools.Pin(**pin) for pin in output.OPiTools.PINLIST]
        gpio = output.OPiTools.GPIOmgr(pins)
        outhelper = output.Outputhelper(gpio)
        t = manager.taskDistributor(logger, successCallback=lambda:unblock(outhelper.enter))
    else:
        t = manager.taskDistributor(logger)
    logger.info("Main process startup complete.")
    nextworker = 0
    try:
        while True:
            f = t.outQ.__getattr__(f"wkr_id{nextworker}")
            t.outQ.__setattr__(f"wkr_id{nextworker}", None)
            if not f is None:
                t.check(f)
            else:
                sleep(0.05)
            nextworker = (nextworker + 1) % int(config['GENERAL']['NUM_WORKERS'])
            t.distribute()
    except KeyboardInterrupt:
        logger.info("Main process shutdown.")
        exit()

if __name__ == "__main__":
    main()
