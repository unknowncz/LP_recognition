from dataclasses import dataclass
from typing import Any
from multiprocessing import Queue
from PyQt6.QtWidgets import QTextEdit, QWidget
import PyQt6.QtCore as QtCore
from subprocess import check_call
from sys import executable
from pkg_resources import working_set
import tensorflow as tf
import numpy as np
import cv2
import threading
import logging.handlers
import logging
import time


@dataclass
class Task:
    '''A dataclass to hold the data for a task to be processed by a worker'''
    id: int
    data: Any
    img: Any=None
    pos:Any=None

# create a stream for the logger to output to the text box
class LoggerOutput(logging.handlers.QueueHandler):
    '''A handler class which writes logging records, appropriately formatted, to a QTextEdit'''
    def __init__(self, queue:Queue=None, *args, reciever_meta:QtCore.QMetaObject, reciever:QTextEdit, formatter:logging.Formatter, **kwargs):
        super().__init__(queue, *args, **kwargs)
        self._queue = queue
        self.reciever_meta = reciever_meta
        self.reciever = reciever
        self.formatter = formatter

    def emit(self, record:logging.LogRecord):
        self.reciever_meta.invokeMethod(self.reciever, 'append', QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, self.formatter.format(record)))

class Detector:
    def __init__(self, path:str, *args, **kwargs):
        try:
            self.model = tf.saved_model.load(path, *args, **kwargs)
            self.wrappedmodel = tf.keras.Sequential()
            self.wrappedmodel.add(tf.keras.layers.Lambda(lambda x: self.model(x)['detection_boxes']))
        except OSError:
            print('Unable to load model')
            self.model = lambda x:x
            self.wrappedmodel = lambda x:x

        self.wrappedmodel.compile()
        self.wrappedmodel.stop_training = True

    def __call__(self, img):
        image_np = np.array(img)
        input_tensor = tf.convert_to_tensor(image_np)
        input_tensor = input_tensor[tf.newaxis, ...]
        detections = self.model(input_tensor)
        return detections

class SubWindow(QWidget):
    def __init__(self, *args, title='SubWindow', **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle(title)

    # hide the window when the minimize button is clicked
    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            if self.windowState() & QtCore.Qt.WindowState.WindowMinimized:
                self.hide()
                event.ignore()

    def closeEvent(self, event):
        self.hide()
        event.ignore()

class FeedManager:
    def __init__(self, logger=logging.getLogger(), *args, **kwargs):
        self.cams = {}
        self.thread = None
        self.logger = logger
        self.stop_feed = False

    def start(self, camcfg:dict):
        self.cam = camcfg
        self.stop_feed = False
        self.thread = threading.Thread(target=self.livefeed_thread, args=(camcfg,), daemon=True)
        self.logger.info(f'Camera {camcfg["id"]} feed started')
        self.thread.start()

    def stop(self):
        self.cam = {}
        self.stop_feed = True
        # self.thread.join()
        self.logger.info('Camera feed stopped')
        cv2.destroyAllWindows()
        self.thread = None

    def livefeed_thread(self, camcfg:dict):
        # cap = cv2.VideoCapture('rtsp://{login}:{password}@{ip}:{port}'.format(**camcfg))
        # capture the video from the camera with a timeout of 5 seconds
        # if the camera connects, the timeout is cancelled
        cap = cv2.VideoCapture('rtsp://{login}:{password}@{ip}:{port}'.format(**camcfg))
        stream_ok = True
        frame_ok = True
        while True:
            try:
                if not cap.isOpened():
                    self.logger.warning(f'Camera {camcfg["id"]} feed stopped - failed to connect')
                    break
                ret, frame = cap.read()
                if self.stop_feed:
                    break
                if ret:
                    if not frame_ok:
                        self.logger.info(f'Camera {camcfg["id"]} feed reestablished')
                    frame_ok = True
                    cv2.imshow(f'Camera {camcfg["id"]} feed', frame)
                else:
                    if frame_ok:
                        self.logger.warning(f'Camera {camcfg["id"]} feed interrupted - no data received')
                    frame_ok = False
            except cv2.error:
                self.logger.warning(f'Camera {camcfg["id"]} feed unavailable - cv2 error')
                break
            if stream_ok:
                if not frame_ok:
                # start of missing video
                    stream_ok = False
                    no_frame_start_time = time.time()
            else:
                if not frame_ok:
                # still no video
                    if time.time() - no_frame_start_time > 5:
                        self.logger.warning(f'Camera {camcfg["id"]} feed timed out - not connected')
                        break
                else:
                # video restarted
                    stream_ok = True
        cap.release()
        cv2.destroyAllWindows()


def crop_image(img, detections, threshold=0.5):
    boxes = detections['detection_boxes'][0].numpy()
    scores = detections['detection_scores'][0].numpy()
    for i, score in enumerate(scores):
        if score > threshold:
            ymin, xmin, ymax, xmax = boxes[i]
            x1, y1, x2, y2 = int(xmin * img.shape[1]), int(ymin * img.shape[0]), int(xmax * img.shape[1]), int(ymax * img.shape[0])
            return img[y1:y2, x1:x2]

