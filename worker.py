import multiprocessing as mp
import numpy as np
import cv2
import easyocr
import time
from dataclasses import dataclass
from typing import Any

@dataclass
class Task:
    id: int
    data: Any


class Worker:
    def __init__(self, qrecv:mp.Queue, qsend:mp.Queue, *_, autostart=False, **__) -> None:
        self._Qrecv = qrecv
        self._Qsend = qsend
        self.reader = easyocr.Reader(['en'])
        if autostart: self.run()

    def run(self):
        while True:
            task:task = self._Qrecv.get()
            img, *pos = anrp(task.data)
            text = get_text(img, self.reader)
            self._Qsend.put(Task(id=task.id, data=text), block=False)


def anrp(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 30, 200)
    cnts = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(c)
            new_img = img[y:y + h, x:x + w]
            break
    # return the cropped image

    return new_img, x, y

def get_text(img, reader: easyocr.Reader):
    img = np.asarray(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    result = reader.readtext(gray, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', detail=0, decoder='greedy')
    return result


if __name__ == '__main__':
    READER = easyocr.Reader(['en'])
    p1 = time.process_time()
    im, x, y = anrp(cv2.imread(f"{__file__}\\..\\LP_Detection\\train\\000f52302c1341eb_jpg.rf.aee8f06b336f83868708a3591d4100b4.jpg"))
    p2 = time.process_time()
    r = get_text(im, READER)
    p3 = time.process_time()
    print(f"Time taken to crop image: {p2 - p1}")
    print(f"Time taken to get text: {p3 - p2}")
    print(r)
    #cv2.imshow('img', im)
    #cv2.waitKey(0)

