# train a model to recognize LPs using detectron2
import os

os.add_dll_directory("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7\\bin")
os.add_dll_directory("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7\\libnvvp")
os.add_dll_directory("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7\\include")

from detectron2.utils.logger import setup_logger
from detectron2.data import MetadataCatalog, DatasetCatalog
import torch
import detectron2


# from google.colab.patches import cv2_imshow
# import some common detectron2 utilities
from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog
from detectron2.data.catalog import DatasetCatalog

from detectron2.data.datasets import register_coco_instances
from detectron2.engine import DefaultTrainer



from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import ColorMode
from detectron2.data import build_detection_test_loader
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.utils.visualizer import Visualizer

import random
import cv2


# import imshow from colab
def imshow(img):
    cv2.imshow('image', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()



setup_logger()
# register the dataset
# https://public.roboflow.com/object-detection/license-plates-us-eu/3
register_coco_instances("license_plates", {}, f"{__file__}\\..\\LP_Detection\\train\\_annotations.coco.json", f"{__file__}\\..\\LP_Detection\\train")
register_coco_instances("license_plates_valid", {}, f"{__file__}\\..\\LP_Detection\\valid\\_annotations.coco.json", f"{__file__}\\..\\LP_Detection\\valid")
register_coco_instances("license_plates_test", {}, f"{__file__}\\..\\LP_Detection\\test\\_annotations.coco.json", f"{__file__}\\..\\LP_Detection\\test")
LP_metadata = MetadataCatalog.get("license_plates")
dataset_dicts = DatasetCatalog.get("license_plates")
# import random
# from detectron2.utils.visualizer import Visualizer
# for d in random.sample(dataset_dicts, 3):
#     img = cv2.imread(d["file_name"])
# visualizer = Visualizer(img[:, :, ::-1], metadata=LP_metadata, scale=0.5)
# vis = visualizer.draw_dataset_dict(d)
# cv2.imshow("imag", vis.get_image()[:, :, ::-1])
cfg = get_cfg()
cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"))
cfg.OUTPUT_DIR = f"{__file__}\\..\\LP_Detection\\output"
# load the custom trained model f"{__file__}\\..\\output"
#cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
cfg.DATASETS.TRAIN = ("license_plates",)
cfg.DATASETS.TEST = ("license_plates_valid",)
cfg.DATALOADER.NUM_WORKERS = 4
# cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml")  # Let training initialize from model zoo


cfg.SOLVER.IMS_PER_BATCH = 10
cfg.SOLVER.BASE_LR = 0.00025  # pick a good LR
cfg.SOLVER.MAX_ITER = 1000    # 300 iterations seems good enough, but you can certainly train longer
cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128   # faster, and good enough for this toy dataset (default: 512)
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 2  # only has one class (license plate)


def train():
    global cfg
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    trainer = DefaultTrainer(cfg)
    trainer.resume_or_load(resume=False)
    print(torch.cuda.is_available())
    trainer.train()

def test():
    global cfg
    cfg.DATASETS.TEST = ("license_plates_test",)
    predictor = DefaultPredictor(cfg)
    for d in random.sample(dataset_dicts, 12):
        im = cv2.imread(d["file_name"])
        outputs = predictor(im)
        v = Visualizer(im,
                   scale=1,
                   instance_mode =  ColorMode.IMAGE
        )
        print(outputs['instances'].pred_classes)
        print(outputs["instances"].pred_boxes.tensor)
        v = v.draw_instance_predictions(outputs["instances"].to("cpu"))
        imshow(v.get_image())
    evaluator = COCOEvaluator("license_plates_test", cfg, False, output_dir=f"{__file__}\\..\\LP_Detection\\output")
    val_loader = build_detection_test_loader(cfg, "license_plates_test")
    inference_on_dataset(predictor.model, val_loader, evaluator)




if __name__ == '__main__':
    # os.environ["CUDA_LAUNCH_BLOCKING"] = "1"


    train()


    # test the model

    # test()







