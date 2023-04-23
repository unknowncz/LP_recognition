import multiprocessing as mp
import numpy as np
import cv2
import cv2.data
import time
import logging
import logging.handlers as log_handlers
import traceback
import paddleocr
OCR = paddleocr.PaddleOCR(lang='en', use_angle_cls=False)

import utils

class Worker:
    def __init__(self, qrecv:mp.Queue, qsend:mp.Queue, loggerQueue=mp.Queue(), detector=utils.Detector(f'{__file__}\\..\\saved_model\\saved_model'), *_, autostart=False, **__) -> None:
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        handler = log_handlers.QueueHandler(loggerQueue)
        self.logger.addHandler(handler)

        self.detector = detector

        self._Qrecv = qrecv
        self._Qsend = qsend
        if autostart: self.run()

    def run(self):
        self.logger.info("Worker started")
        while True:
            try:
                task:utils.Task = self._Qrecv.get()
                box, score, *_ = self.detector(task.data)
                img = task.data
                if score > 0.5:
                    img = img[box[1]:box[3], box[0]:box[2]]
                    pos = (box[0], box[1], box[2]-box[0], box[3]-box[1])
                else:
                    pos = (0,0,img.shape[1],img.shape[0])
                text = get_text(img)
                self._Qsend.put(utils.Task(id=task.id, data=text, pos=pos), block=False)
            except Exception as e:
                self.logger.error(f"Exception in worker", extra={'traceback':traceback.format_exc()})
                if type(e) == KeyboardInterrupt:
                    break


def get_text(img, ocr=OCR):
    img = np.asarray(img)
    result = ocr.ocr(img, cls=True)
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
    detector = utils.Detector(f'{__file__}\\..\\saved_model\\saved_model')

    img = cv2.imread(f"{__file__}\\..\\LP_Detection\\train\\4a71f2d037c2af0b_jpg.rf.4e2d6ddd617d92cd766575c9ad97bef3.jpg")
    # img = cv2.imread(f"{__file__}\\..\\test17.jpg")

    # cv2.imshow('img', img)
    # cv2.waitKey(0)
    p1 = time.process_time()
    detections = detector(img)
    # crop the image to the number plate with the highest confidence
    im = utils.crop_image(img, detections)

    p2 = time.process_time()

    r = get_text(im)
    p3 = time.process_time()
    print(f"Time taken to crop image: {p2 - p1}")
    print(f"Time taken to get text: {p3 - p2}")
    print(r)

    # gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    # gray = cv2.medianBlur(gray, 3)
    # still_gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    # ret, still_gray = cv2.threshold(still_gray, 127, 255, cv2.THRESH_BINARY)
    # kernel = np.ones((2,2),np.uint8)
    # still_gray = cv2.erode(still_gray,kernel,iterations = 1)
    cv2.imshow('img', im)
    cv2.waitKey(0)

