from multiprocessing import Queue
import numpy as np
import cv2
import logging
from logging.handlers import QueueHandler
import traceback
import paddleocr
import os
if __name__ == "__main__":
    import time

OCR = paddleocr.PaddleOCR(lang='en', use_angle_cls=False)
SELFDIR = os.path.abspath(f'{__file__}/..')

import utils

class Worker:
    """A worker class to process tasks from a queue and put the results in another queue
    """
    def __init__(self, qrecv:Queue, qsend:Queue, loggerQueue=Queue(), *_, model_type='lite', model_pth=None, autostart=False, **__) -> None:
        """Initialize the worker

        Args:
            qrecv (Queue): Receiver queue for communication.
            qsend (Queue): Transmitter queue for communication.
            loggerQueue (Queue, optional): Queue for logging connections. Defaults to multiprocessing.Queue().
            detector (utils.Detector, optional): Licence Plate detector class. Defaults to utils.Detector(f'{__file__}\..\saved_model\saved_model').
            autostart (bool, optional): Automatically start the main loop, if set to false, the 'run' method needs to be called separately. Defaults to False.
        """
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        handler = QueueHandler(loggerQueue)
        self.logger.addHandler(handler)

        pth = f"{SELFDIR}/saved_model"
        if model_pth is not None:
            self.logger.info(f"Using custom model at {model_pth}")
            pth = model_pth

        # setup detection model
        if model_type == 'tf':
            self.logger.info("Using TensorFlow model")
            self.detector = utils.Detector(f"{pth}/saved_model")
        elif model_type == 'lite':
            self.logger.info("Using TensorFlow Lite model")
            self.detector = utils.LiteDetector(f"{pth}/model.tflite")
        else:
            self.logger.error("Invalid model type")
            exit(1)

        self._Qrecv = qrecv
        self._Qsend = qsend
        if autostart: self.run()

    def run(self):
        """Main loop of the worker.
        """
        self.logger.info("Worker started")
        while True:
            text = []
            try:
                task:utils.Task = self._Qrecv.get()
                if task.data is not None:
                    detections = self.detector(task.data)
                    img = utils.crop_image(task.data, detections, threshold=0.2)
                    if img is not None and len(img) > 0:
                        #imgmean = np.mean(img)
                        #_, img = cv2.threshold(img, imgmean, 255, cv2.THRESH_BINARY)
                        #cv2.imshow("img", img)
                        #cv2.waitKey(1)
                        text = get_text(img)
            except Exception as e:
                self.logger.error(f"Exception in worker:")
                self.logger.error(traceback.format_exc())
                if type(e) == KeyboardInterrupt:
                    break
            self._Qsend.put(utils.Task(id=task.id, data=text))

def get_text(img, ocr=OCR):
    """Get text from an image.

    Args:
        img (numpy.ndarray): Image for text extraction
        ocr (paddleocr.PaddleOCR, optional): OCR model for detection. Defaults to OCR.

    Returns:
        list: Extracted text with bbox and confidence
    """
    img = np.asarray(img)
    result = ocr.ocr(img, cls=False)
    result = result[0]
    # clean up the result
    # make sure the text only contains alphanumeric characters
    # result format: [bbox, (text, confidence)]
    for i in range(len(result)):
        result[i] = [result[i][0], (''.join([c for c in result[i][1][0] if c.isalnum()]), result[i][1][1])]
    # result[1] = (''.join([c for c in result[1][0] if c.isalnum()]), result[1][1])

    return result


if __name__ == '__main__':
    print("-------------------")
    detector = utils.Detector(f'{SELFDIR}/saved_model/saved_model')

    img = cv2.imread(f"{SELFDIR}/LP_Detection/train/1af54be605a0f1d5_jpg.rf.34325727380de220fcd244b900430c97.jpg")
    # img = cv2.imread(f"{SELFDIR}/test17.jpg")

    # cv2.imshow('img', img)
    # cv2.waitKey(0)
    p1 = time.process_time()
    detections = detector(img)
    # crop the image to the number plate with the highest confidence
    p2 = time.process_time()

    im = utils.crop_image(img, detections)

    p3 = time.process_time()

    r = get_text(im)
    p4 = time.process_time()
    print(f"Time taken to get detections from image: {p2 - p1}")
    print(f"Time taken to crop image: {p3 - p2}")
    print(f"Time taken to get text: {p4 - p3}")
    print(r)

    # gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    # gray = cv2.medianBlur(gray, 3)
    # still_gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    # ret, still_gray = cv2.threshold(still_gray, 127, 255, cv2.THRESH_BINARY)
    # kernel = np.ones((2,2),np.uint8)
    # still_gray = cv2.erode(still_gray,kernel,iterations = 1)
    cv2.imshow('img', im)
    cv2.waitKey(0)

