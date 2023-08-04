from multiprocessing import Queue, queues
import cv2
import logging
from logging.handlers import QueueHandler
import traceback

import utils

class Camera:
    """A class to represent a camera and its connection to the system.
    """
    def __init__(self, cfg:dict, output=Queue(), loggerQueue=Queue(), autoconnect=False):
        """Initialize the class. If autoconnect is set to True, the camera will connect automatically.

        Args:
            cfg (dict): Camara config as a dictionary.
            output (Queue, optional): Queue for the camera frames. Defaults to multiprocessing.Queue().
            loggerQueue (Queue, optional): Queue for logging connections. Defaults to multiprocessing.Queue().
            autoconnect (bool, optional): Automatically connect to the camera. Defaults to False.
        """
        # add logging and logging queue
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(QueueHandler(loggerQueue))

        self.cfg = cfg
        self._output = output

        if autoconnect:
            self.connect(autostart=True)

    def connect(self, autostart=False):
        """Connect to the camera. If autostart is set to True, the camera will start sending frames to the output queue.

        Args:
            autostart (bool, optional): Start automatically after connecting. Defaults to False.
        """
        # self.logger.info(f"Connecting to camera {self.cfg['id']} at {self.cfg['ip']}:{self.cfg['port']}")
        self.logger.info("Connecting to camera {id} at {ip}:{port}".format(**self.cfg))

        # self._vcap = cv2.VideoCapture(f"{self.cfg['protocol']}://{self.cfg['login']}:{self.cfg['password']}@{self.cfg['ip']}:{int(self.cfg['port'])}")
        self._vcap = cv2.VideoCapture("{protocol}://{login}:{password}@{ip}:{port}".format(**self.cfg))
        try:
            ret ,_= self._vcap.read()
            if not ret:
                self.logger.error(f"Failed to connect to camera {self.cfg['id']}", extra={'traceback':traceback.format_exc()})
                exit(1)
        except:traceback.print_exc();return

        if autostart:
            self.run()

    def run(self):
        """Start sending frames to the output queue.
        """
        ret2 = False
        while True:
            try:
                ret, frame = self._vcap.read()
                if not ret:
                    if not ret2:
                        self.logger.warning('Failed to grab frame')
                    ret2 = True
                elif ret2:
                    self.logger.info('Camera is back online')
                    ret2 = False
                try:
                    self._output.put_nowait(utils.Task(self.cfg['id'], frame))
                except queues.Full:
                    pass
            except Exception as e:
                self.logger.error(f"Failed to read from camera {self.cfg['id']}")
                self.logger.error(traceback.format_exc())
                if type(e) == KeyboardInterrupt:
                    break

        self._vcap.release()

    def __delete__(self):
        self._vcap.release()
