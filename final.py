import numpy
import cv2

import easyocr

def anrp(img):
    # img = cv2.imread(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 30, 200)
    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]
    count = 0
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:  # Select the contour with 4 corners
            x, y, w, h = cv2.boundingRect(c)  # This is our approx Number Plate Contour
            new_img = img[y:y + h, x:x + w]
            count += 1
            break
    # return the cropped image
    return new_img


def print_result(result):
    for detection in result:
        print(detection)

def get_text(img):
    img = numpy.array(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # cv2.imshow('img', img)
    # cv2.waitKey(0)

    # convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # cv2.imshow('gray', gray)
    # cv2.waitKey(0)

    # get the text from the image
    reader = easyocr.Reader(['en'])
    result = reader.readtext(gray)

    print('here')
    print(result)
    cv2.imshow('img', img)
    cv2.waitKey(0)

if __name__ == '__main__':
    im = anrp(cv2.imread(f"{__file__}\\..\\LP_Detection\\train\\44afab29f5fa0abf_jpg.rf.f3680323d7d57bd04e10f87c8fe3e8b0.jpg"))
    get_text(im)
