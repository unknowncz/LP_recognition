from multiprocessing import Queue, queues, Manager
import cv2
import logging
from logging.handlers import QueueHandler
import traceback
import time

import utils

NUM_RETRIES = 5
RETRY_INTERVAL = 60

class Camera:
    """A class to represent a camera and its connection to the system.
    """
    def __init__(self, cfg:dict, output, loggerQueue=Queue(), autoconnect=False):
        """Initialize the class. If autoconnect is set to True, the camera will connect automatically.

        Args:
            cfg (dict): Camara config as a dictionary.
            output (Namespace): Multiprocessing namespace, Stores the current frame in the 'cam_id{camera_id}' variable.
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
        connected = False
        attempt = 0
        while not connected and attempt < NUM_RETRIES:
            try:
                ret ,_= self._vcap.read()
                if not ret:
                    self.logger.critical(f"Failed to connect to camera {self.cfg['id']}, attempt: {attempt}")
                    attempt += 1
                    time.sleep(RETRY_INTERVAL)
                    continue
                connected = True
            except:traceback.print_exc();return
        if not connected:
            self.logger.error(f"Failed to connect to canera {self.cfg['id']}, out of retries")
            exit()
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

                setattr(self._output, f"cam_id{self.cfg['id']}", utils.Task(self.cfg['id'], frame))


            except Exception as e:
                self.logger.error(f"Failed to read from camera {self.cfg['id']}")
                self.logger.error(traceback.format_exc())
                setattr(self._output, f"id{self.cfg['id']}", [])
                if type(e) == KeyboardInterrupt:
                    break

        self._vcap.release()

    def __delete__(self):
        self._vcap.release()
