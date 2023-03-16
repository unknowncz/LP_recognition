import multiprocessing as mp
import numpy as np
import cv2
import cv2.data
import easyocr
import time
import logging
import logging.handlers as log_handlers
import traceback
import tensorflow as tf

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
        self.reader = easyocr.Reader(['en'])
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
                text = get_text(img, self.reader)
                self._Qsend.put(utils.Task(id=task.id, data=text, pos=pos), block=False)
            except Exception as e:
                self.logger.error(f"Exception in worker", extra={'traceback':traceback.format_exc()})
                if type(e) == KeyboardInterrupt:
                    break

# old code
def keep(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_russian_plate_number.xml")
    plates = cascade.detectMultiScale(gray, 1.2, 5)
    print('Number of detected license plates:', len(plates))
    for (x,y,w,h) in plates:
        # draw bounding rectangle around the license number plate
        cv2.rectangle(img, (x,y), (x+w, y+h), (0,255,0), 2)
        gray_plates = gray[y:y+h, x:x+w]
        color_plates = img[y:y+h, x:x+w]

        # cv2.imshow('Number Plate', color_plates)
        # cv2.imshow('Number Plate', gray_plates)
        # cv2.imshow('Number Plate Image', img)
        # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    if len(plates) == 0:
        # default return - no plate detected, return original image and (0,0) for x,y coordinates and the size of the image (w,h)
        return img, (0,0,img.shape[1],img.shape[0])
    return color_plates, (x,y,w,h)

def get_text(img, reader: easyocr.Reader):
    img = np.asarray(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    result = reader.readtext(gray, allowlist='ABCDEFHIJKLMNPRSTUVXYZ0123456789', detail=0, decoder='greedy')
    return result


def test():
    coco_annotation_file_path = f"{__file__}\\..\\LP_Detection\\train\\_annotations.coco.json"

    coco_annotation = 0
    # coco_annotation = pycocotools.coco.COCO(annotation_file=coco_annotation_file_path)

    # Category IDs.
    cat_ids = coco_annotation.getCatIds()
    print(f"Number of Unique Categories: {len(cat_ids)}")
    print("Category IDs:")
    print(cat_ids)  # The IDs are not necessarily consecutive.

    # All categories.
    cats = coco_annotation.loadCats(cat_ids)
    cat_names = [cat["name"] for cat in cats]
    print("Categories Names:")
    print(cat_names)

    # Category ID -> Category Name.
    query_id = cat_ids[0]
    query_annotation = coco_annotation.loadCats([query_id])[0]
    query_name = query_annotation["name"]
    query_supercategory = query_annotation["supercategory"]
    print("Category ID -> Category Name:")
    print(
        f"Category ID: {query_id}, Category Name: {query_name}, Supercategory: {query_supercategory}"
    )

    # Category Name -> Category ID.
    query_name = cat_names[1]
    query_id = coco_annotation.getCatIds(catNms=[query_name])[0]
    print("Category Name -> ID:")
    print(f"Category Name: {query_name}, Category ID: {query_id}")

    # Get the ID of all the images containing the object of the category.
    img_ids = coco_annotation.getImgIds(catIds=[query_id])
    print(f"Number of Images Containing {query_name}: {len(img_ids)}")

    # Pick one image.
    img_id = img_ids[2]
    img_info = coco_annotation.loadImgs([img_id])[0]
    img_file_name = img_info["file_name"]
    print(
        f"Image ID: {img_id}, File Name: {img_file_name}"
    )

    # Get all the annotations for the specified image.
    ann_ids = coco_annotation.getAnnIds(imgIds=[img_id], iscrowd=None)
    anns = coco_annotation.loadAnns(ann_ids)
    print(f"Annotations for Image ID {img_id}:")
    print(anns)

    # Use URL to load image.
    # im = Image.open(f'{__file__}\\..\\LP_Detection\\train\\{img_file_name}')

    # Save image and its labeled version.
    # plt.axis("off")
    # plt.imshow(np.asarray(im))
    # plt.savefig(f"{img_id}.jpg", bbox_inches="tight", pad_inches=0)
    # Plot segmentation and bounding box.
    # coco_annotation.showAnns(anns, draw_bbox=True)
    # plt.savefig(f"{img_id}_annotated.jpg", bbox_inches="tight", pad_inches=0)

if __name__ == '__main__':
    # test()
    print("-------------------")
    READER = easyocr.Reader(['en'])
    # dataset is in /LP_Detection/train in the Coco format
    # load the dataset
    # coco_annotation_file_path = f"{__file__}\\..\\LP_Detection\\train\\_annotations.coco.json"

    # coco_annotation = pycocotools.coco.COCO(annotation_file=coco_annotation_file_path)
    # coco_annotation.info()

    # Category IDs.
    # cat_ids = coco_annotation.getCatIds()
    # print(f"Number of Unique Categories: {len(cat_ids)}")
    # print("Category IDs:")
    # print(cat_ids)
    # cats = coco_annotation.loadCats(cat_ids)
    # cat_names = [cat["name"] for cat in cats]
    # print("Category Names:")
    # print(cat_names)
    detector = utils.Detector(f'{__file__}\\..\\saved_model\\saved_model')
    import matplotlib.pyplot as plt

    img = cv2.imread(f"{__file__}\\..\\LP_Detection\\train\\00d763761e47f723_jpg.rf.d730edd1f70faf90c6bb817837445b17.jpg")
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    cv2.imshow('img', img)
    cv2.waitKey(0)
    p1 = time.process_time()
    detections = detector(img)
    # crop the image to the number plate with the highest confidence
    im = utils.crop_image(img, detections)

    p2 = time.process_time()
    r = get_text(im, READER)
    p3 = time.process_time()
    print(f"Time taken to crop image: {p2 - p1}")
    print(f"Time taken to get text: {p3 - p2}")
    print(r)
    cv2.imshow('img', im)
    cv2.waitKey(0)

