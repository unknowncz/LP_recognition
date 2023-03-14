from dataclasses import dataclass
from typing import Any
from multiprocessing import Queue
from PyQt6.QtWidgets import QTextEdit, QWidget
import PyQt6.QtCore as QtCore
from subprocess import check_call
from sys import executable
from pkg_resources import working_set
import tensorflow as tf
from numpy import array, int64
import cv2
import threading
import logging.handlers
import logging
import asyncio
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
        except OSError:
            print('Unable to load model')
            self.model = lambda x:x

    def __call__(self, img):
        image_np = array(img)
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
        self.threads = {}
        self.logger = logger

    def add(self, camcfg:dict):
        self.cams[str(camcfg['id'])] = camcfg
        self.threads[str(camcfg['id'])] = threading.Thread(target=self.livefeed_thread, args=(camcfg,))
        self.threads[str(camcfg['id'])].start()
        self.logger.info(f'Camera {camcfg["id"]} feed started')

    def remove(self, camcfg:dict):
        self.cams.pop(str(camcfg['id']))
        self.threads[str(camcfg['id'])].stop()
        self.threads.pop(str(camcfg['id']))
        self.logger.info(f'Camera {camcfg["id"]} feed stopped')

    def timedOut(self, thread:threading.Thread, camcfg:dict):
        self.logger.warning(f'Camera {camcfg["id"]} feed timed out - not connected')
        thread.stop()
        self.remove(camcfg)

    def livefeed_thread(self, camcfg:dict):
        # self.threads[str(camcfg['id'])]
        t = Timeout(self.threads[str(camcfg['id'])], camcfg, 10)
        asyncio.run(t())
        cap = cv2.VideoCapture('rtsp://{login}:{password}@{ip}:{port}'.format(**camcfg))
        t.cancel()

        while True:
            ret, frame = cap.read()
            if ret:
                cv2.imshow(f'Camera {camcfg["id"]}', frame)
            else:
                self.logger.warning(f'Camera {camcfg["id"]} feed stopped - no data received')
                break
        cap.release()
        self.remove(camcfg)

class Timeout:
    def __init__(self, cfg, target, timeout, callback=lambda *x:None):
        self.target = target
        self.timeout = timeout
        self.callback = callback
        self.canceled = False
        self.cfg = cfg

    async def __call__(self, *args, **kwargs):
        await asyncio.sleep(self.timeout)
        if not self.canceled:
            self.callback(self.target, self.cfg)

    def cancel(self):
        self.canceled = True


def crop_image(img, detections, threshold=0.5):
    boxes = detections['detection_boxes'][0].numpy()
    scores = detections['detection_scores'][0].numpy()
    for i, score in enumerate(scores):
        if score > threshold:
            ymin, xmin, ymax, xmax = boxes[i]
            x1, y1, x2, y2 = int(xmin * img.shape[1]), int(ymin * img.shape[0]), int(xmax * img.shape[1]), int(ymax * img.shape[0])
            return img[y1:y2, x1:x2]
    return img

def check_modules(required:list[str], logger=logging.getLogger()):
    '''Check if required modules are installed, if not, attempt to install them'''
    INSTALLED = {*(pkg.key for pkg in working_set if pkg.key)}
    if MISSING:=[m for m in required if m.lower() not in INSTALLED]:
        if len(MISSING) > 1:
            logger.warning(f'MISSING MODULES {", ".join(MISSING)}. ATTEMPTING AUTO-IMPORT')
        else:
            logger.warning(f'MISSING MODULE {MISSING[0]}. ATTEMPTING AUTO-IMPORT')
        PYTHON = executable
        check_call([PYTHON, '-m', 'pip', 'install', '--upgrade', *(MISSING + [])])

