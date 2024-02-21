from dataclasses import dataclass
from typing import Any
from multiprocessing import Queue
from PyQt5.QtWidgets import QTextEdit, QMdiSubWindow, QLabel
from PyQt5 import Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from tensorflow import keras, saved_model, convert_to_tensor, newaxis, lite
from threading import Thread
from logging.handlers import QueueHandler
import logging
import numpy as np
import cv2
from time import time
import sys


@dataclass
class Task:
    """Task utilized when transporting data between processes
    """
    id: int
    data: Any

# create a stream for the logger to output to the text box
class LoggerOutput(QueueHandler):
    """A handler class which writes logging records, appropriately formatted, to a QTextEdit
    """
    def __init__(self, queue:Queue=None, *args, reciever_meta:QtCore.QMetaObject, reciever:QTextEdit, formatter:logging.Formatter, **kwargs):
        """Initialize the class.

        Args:
            reciever_meta (QtCore.QMetaObject): QTextEdit meta element, which the logger will output to.
            reciever (QTextEdit): QTextEdit element, which the logger will output to.
            formatter (logging.Formatter): Logging formatter to be used for the logs
            queue (Queue, optional): Queue which the logger will recieve logs from. Defaults to None.
        """
        super().__init__(queue, *args, **kwargs)
        self._queue = queue
        self.reciever_meta = reciever_meta
        self.reciever = reciever
        self.formatter = formatter

    def emit(self, record:logging.LogRecord):
        """Logger emit function override.

        Args:
            record (logging.LogRecord): LogRecord to be processed
        """
        self.reciever_meta.invokeMethod(self.reciever, 'append', QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, self.formatter.format(record)))

class Detector:
    """Wrapper detector class for the Tensorflow model
    """
    def __init__(self, path:str, *args, **kwargs):
        """Initialize the class and load the model

        Args:
            path (str): Path to the model for license plate detection
        """
        try:
            self.model = saved_model.load(path, *args, **kwargs)
            self.wrappedmodel = keras.Sequential()
            self.wrappedmodel.add(keras.layers.Lambda(lambda x: self.model(x)['detection_boxes']))
        except OSError:
            self.logger.error('Unable to load model')
            self.model = lambda x:x
            self.wrappedmodel = lambda x:x

        self.wrappedmodel.compile()
        self.wrappedmodel.stop_training = True

    def __call__(self, img):
        """Detect license plates in the image

        Args:
            img (np.ndarray): Image to be processed

        Returns:
            tensor: Tensor containing the bounding boxes of the detected license plates
        """
        image_np = np.array(img)
        input_tensor = convert_to_tensor(image_np)
        input_tensor = input_tensor[newaxis, ...]
        detections = self.model(input_tensor)
        return detections

class LiteDetector(Detector):
    def __init__(self, path: str, *args, **kwargs):
        """Initialize the class and load the model

        Args:
            path (str): Path to the model for license plate detection
        """
        self.interpreter = lite.Interpreter(model_path=path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def __call__(self, img):
        """Detect license plates in the image

        Args:
            img (np.ndarray): Image to be processed

        Returns:
            tensor: Tensor containing the bounding boxes of the detected license plates
        """
        img = cv2.resize(img, (640, 640))
        image_np = np.array(img)
        image_np = (image_np / 255).astype(np.float32)
        input_tensor = convert_to_tensor(image_np)
        input_tensor = input_tensor[newaxis, ...]
        self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
        self.interpreter.invoke()
        conf = self.interpreter.get_tensor(self.output_details[0]['index'])
        boxes = self.interpreter.get_tensor(self.output_details[1]['index'])
        return {'detection_scores':conf, 'detection_boxes':boxes}


class FeedManager:
    """Feed manager class for managing the live feeds
    """
    def __init__(self, logger=logging.getLogger(), *args, **kwargs):
        """Initialize the class.

        Args:
            logger (logging.Logger, optional): Logger. Defaults to logging.getLogger().
        """
        self.thread = None
        self.logger = logger
        self.stop_feed = False

    def start(self, camcfg:dict, crop=False):
        """Starts the live feed for the camera

        Args:
            camcfg (dict): Camera configuration dictionary
            crop (bool): Enable camera image cropping feature
        """
        # stop the feed if it is already running this would cause issues if the thread is not stopped before starting a new one
        if self.thread:
            self.stop()

        self.cam = camcfg
        self.stop_feed = False
        self.thread = Thread(target=self.livefeed_thread, args=(camcfg,crop), daemon=True)
        self.logger.info(f'Camera {camcfg["id"]} feed started')
        self.thread.start()

    def stop(self):
        """Stops the live feed for the camera
        """
        self.cam = {}
        self.stop_feed = True
        self.logger.info('Camera feed stopped')

    def livefeed_thread(self, camcfg:dict, crop=False):
        """Live feed thread function. Opens the live feed for the camera and displays it in a window.

        Args:
            camcfg (dict): Camera configuration dictionary
            crop (bool): Enable camera image cropping feature
        """
        # re-implement the livefeed_thread function for linux (use qt as opencv-headless is not available)
        cap = cv2.VideoCapture('{protocol}://{login}:{password}@{ip}:{port}'.format(**camcfg))
        stream_ok = True
        frame_ok = True
        frameshape = cap.read().shape

        if crop:
            temp = camcfg.get("crop", [0, 0, frameshape[1], frameshape[0]])
            self.crop = [temp[0] or 0, temp[1] or 0, temp[2] or frameshape[1], temp[3] or frameshape[0]]
            self.tempcrop = []
        imgvwr = QLabel()
        window = QMdiSubWindow()
        window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        window.setWindowTitle(f'Camera {camcfg["id"]} feed')
        # when the window is closed, stop the feed
        window.closeEvent = lambda event: self.stop()
        window.show()
        window.setWidget(imgvwr)
        # if the crop option is set, crop the image on drag
        if crop:
            # on right click reset the crop to the entire image
            # on drag, crop the image to a rectangle between the two points
            # store the start point of the crop
            def mousePressEvent(event):
                if event.button() == Qt.LeftButton:
                    self.crop_start = event.pos()
                elif event.button() == Qt.RightButton:
                    del self.crop_start
                    self.crop = [0, 0, frameshape[1], frameshape[0]]
            # store the end point of the crop and crop the image
            def mouseReleaseEvent(event):
                if not self.crop_start:
                    return
                self.crop_end = event.pos()
                x1, y1 = self.crop_start.x(), self.crop_start.y()
                x2, y2 = self.crop_end.x(), self.crop_end.y()
                x, y = min(x1, x2), min(y1, y2)
                w, h = abs(x1 - x2), abs(y1 - y2)
                self.crop = [x, y, w, h]
            # add a mouse move event to the image viewer - draw a rectangle from the start point to the current point
            def mouseMoveEvent(event):
                if hasattr(self, 'crop_start'):
                    x1, y1 = self.crop_start.x(), self.crop_start.y()
                    x2, y2 = event.pos().x(), event.pos().y()
                    x, y = min(x1, x2), min(y1, y2)
                    w, h = abs(x1 - x2), abs(y1 - y2)
                    self.tempcrop = [x, y, w, h]

            # add a mouse press and release event to the image viewer
            imgvwr.mousePressEvent = mousePressEvent
            imgvwr.mouseReleaseEvent = mouseReleaseEvent
            imgvwr.mouseMoveEvent = mouseMoveEvent

        while not self.stop_feed:
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
                    # if the crop option is set, draw a rectangle to show the crop area
                    if self.crop:
                        x, y, w, h = self.crop
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    if self.tempcrop:
                        x, y, w, h = self.tempcrop
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (127, 127, 255), 3)
                    imgvwr.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()))
                elif frame_ok:
                    self.logger.warning(f'Camera {camcfg["id"]} feed interrupted - no data received')
                    frame_ok = False
            except cv2.error:
                self.logger.warning(f'Camera {camcfg["id"]} feed unavailable - cv2 error')
                break
            if stream_ok:
                if not frame_ok:
                # start of missing video
                    stream_ok = False
                    no_frame_start_time = time()
            else:
                if not frame_ok:
                # still no video
                    if time() - no_frame_start_time > 5:
                        self.logger.warning(f'Camera {camcfg["id"]} feed timed out - not connected')
                        break
                else:
                # video restarted
                    stream_ok = True
        cap.release()
        window.close()
        self.thread = None


def crop_image(img, detections, threshold=0.5):
    """Crops the image to the bounding box of the detected license plate.

    Args:
        img (np.ndarray): Image to be processed.
        detections (Tensor): Tensor containing the bounding boxes of the detected license plates.
        threshold (float, optional): Required threshold for the detection to pass. Defaults to 0.5.

    Returns:
        np.ndarray: Cropped image
    """
    boxes = detections['detection_boxes'][0]
    scores = detections['detection_scores'][0]

    max_score = max(enumerate(scores), key=lambda x:x[1])
    if max_score[1] < threshold:
        return None
    ymin, xmin, ymax, xmax = boxes[max_score[0]]
    x1, y1, x2, y2 = int(xmin * img.shape[1]), int(ymin * img.shape[0]), int(xmax * img.shape[1]), int(ymax * img.shape[0])
    return img[y1:y2, x1:x2]

def joinpredictions(task:Task):
    """Joins the predictions of the task from list[bbox, (prediction, confidence))] to [bbox, prediction, confidence]

    Args:
        task (Task): Input task containing a list of predictions

    Returns:
        Task: Output task containing a list of predictions of length 1
    """

    conf = np.average([pred[1][1] for pred in task.data])
    text = ''.join([pred[1][0] for pred in task.data if pred[1][1] > 0.5])
    # calculate the bounding box of the license plate from the bounding boxes of the different predictions
    bbox = [min([pred[0][0] for pred in task.data]), min([pred[0][1] for pred in task.data]), max([pred[0][2] for pred in task.data]), max([pred[0][3] for pred in task.data])]
    return Task(task.id, data=[bbox, (text, conf)])
