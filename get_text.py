import numpy
import cv2
import easyocr

# create a text recognition model with easyocr

# print a sample image with its label

# load the image and find the license plate
origimg = cv2.imread(f"{__file__}\\..\\test.jpg")
img = numpy.array(origimg)
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

def print_result(result):
    for detection in result:
        print(detection[1])

print_result(result)
cv2.imshow('img', img)
cv2.waitKey(0)



