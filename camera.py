import multiprocessing as mp
import cv2
import logging
from logging.handlers import QueueHandler
import traceback


import utils

class Camera:
    """A class to represent a camera and its connection to the system.
    """
    def __init__(self, id=-1, address=('127.0.0.1', 80), output=mp.Queue(), loggerQueue=mp.Queue(), autoconnect=False, login='admin', password='admin'):
        """Initialize the class. If autoconnect is set to True, the camera will connect automatically.

        Args:
            id (int, optional): Camera ID. Defaults to -1.
            address (tuple, optional): IP ad. Defaults to ('127.0.0.1', 80).
            output (mp.Queue, optional): Queue for the camera frames. Defaults to mp.Queue().
            loggerQueue (mp.Queue, optional): Queue for logging connections. Defaults to mp.Queue().
            autoconnect (bool, optional): Automatically connect to the camera. Defaults to False.
            login (str, optional): Login username to use when connecting. Defaults to 'admin'.
            password (str, optional): Password to use when connecting. Defaults to 'admin'.
        """
        # add logging and logging queue
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(QueueHandler(loggerQueue))

        self._id = id
        self._address = address
        self._output = output

        self.login = login
        self.password = password
        if autoconnect:
            self.connect(autostart=True)

    def connect(self, autostart=False):
        """Connect to the camera. If autostart is set to True, the camera will start sending frames to the output queue.

        Args:
            autostart (bool, optional): Start automatically after connecting. Defaults to False.
        """
        self.logger.info(f"Connecting to camera {self._id} at {self._address[0]}:{self._address[1]}")

        self._vcap = cv2.VideoCapture(f"rtsp://{self.login}:{self.password}@{self._address[0]}:{int(self._address[1])}")
        try:
            ret ,_= self._vcap.read()
            if not ret:
                self.logger.error(f"Failed to connect to camera {self._id}", extra={'traceback':traceback.format_exc()})
                return
        except:traceback.print_exc();return


        if autostart:
            self.run()

    def run(self):
        """Start sending frames to the output queue.
        """
        # files = [f for f in os.listdir(f"{__file__}\\..\\LP_Detection\\train")]
        # i = 0
        while True:

            # frame = cv2.imread(f"{__file__}\\..\\LP_Detection\\train\\{files[i]}")
            # if not files[i].endswith(".jpg"): continue
            # try:
            #     self._output.put_nowait(Task(self._id, frame))
            #     # print(f"Added task {i}")
            #     i += 1
            #     if i >= len(files)-2: i=0
            # except mp.queues.Full:
            #     pass
            # continue
            try:
                ret, frame = self._vcap.read()
                if not ret:
                    self.logger.critical('Failed to grab frame')
                    break
                try:
                    self._output.put_nowait(utils.Task(self._id, frame))
                except mp.queues.Full:
                    pass
            except Exception as e:
                self.logger.error(f"Failed to read from camera {self._id}", extra={'traceback':e.with_traceback()})
                if type(e) == KeyboardInterrupt:
                    break

        self._vcap.release()

    def __delete__(self):
        self._vcap.release()



if __name__ == "__main__":
    cam = Camera(0, "192.168.1.150", 554)
    cam.connect(True, login='admin', password='admin')
