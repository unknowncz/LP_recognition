import os
import math
import random
import numpy
import torch
import torchvision
import torchvision.transforms as transforms
import cv2
import easyocr

os.add_dll_directory("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7\\bin")
os.add_dll_directory("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7\\libnvvp")
os.add_dll_directory("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7\\include")

datadir = os.path.abspath(f'{__file__}\\..\\LP_Recognition\\dataset_coco')
output_dir = os.path.abspath(f'{__file__}\\..\\LP_Recognition\\output')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# letters_label_map.pbtxt

# create a text recognition model with easyocr

# load coco dataset of images size 640x640
traindataset = torchvision.datasets.CocoDetection(root=f'{datadir}\\train\\', annFile=f'{datadir}\\train\\_annotations.coco.json')
valdataset = torchvision.datasets.CocoDetection(root=f'{datadir}\\valid\\', annFile=f'{datadir}\\valid\\_annotations.coco.json')

# print a sample image with its label
import cv2

origimg, label = traindataset[math.floor(random.random() * len(traindataset))]
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



