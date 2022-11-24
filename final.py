import os

os.add_dll_directory("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7\\bin")
os.add_dll_directory("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7\\libnvvp")
os.add_dll_directory("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7\\include")

from detectron2.utils.logger import setup_logger

import numpy
import torch
import cv2

from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import ColorMode
from detectron2.utils.visualizer import Visualizer

import easyocr


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
setup_logger()

def imshow(img):
    cv2.imshow('image', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


cfg = get_cfg()
cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"))
cfg.OUTPUT_DIR = f"{__file__}\\..\\LP_Detection\\output"
# load the custom trained model f"{__file__}\\..\\output"
cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
cfg.DATASETS.TRAIN = ("license_plates",)
cfg.DATASETS.TEST = ("license_plates_valid",)
cfg.DATALOADER.NUM_WORKERS = 4
# cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml")  # Let training initialize from model zoo
cfg.SOLVER.IMS_PER_BATCH = 10
cfg.SOLVER.BASE_LR = 0.00025  # pick a good LR
cfg.SOLVER.MAX_ITER = 1000    # 300 iterations seems good enough, but you can certainly train longer
cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128   # faster, and good enough for this toy dataset (default: 512)
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 2  # only has one class (license plate)

def predict(img):
    global cfg
    predictor = DefaultPredictor(cfg)
    outputs = predictor(img)
    v = Visualizer(img,
                   scale=1,
                   instance_mode=ColorMode.IMAGE
                   )
    print(outputs['instances'].pred_classes)
    print(outputs["instances"].pred_boxes.tensor)
    return outputs["instances"].pred_boxes.tensor


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
    im = predict(cv2.imread(f"{__file__}\\..\\test.jpg"))
    # cut down the image to the license plate
    imc = cv2.imread(f"{__file__}\\..\\test.jpg").copy()[int(im[0][0]):int(im[0][2]), int(im[0][1]):int(im[0][3])]
    get_text(imc)
