import multiprocessing as mp
from sys import stdout
import configparser
import logging
from logging.handlers import QueueHandler, QueueListener
import cv2

import utils

# TODO:
#  - GUI - config control, camera control, worker control
#  - Logging - finalise logging system (last thing to do)
#  - Config file saving - save config file on exit

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO, filename=f"{__file__}\\..\\log", filemode='w')
    logger.addHandler(logging.StreamHandler(stdout))
    logger.info("Loading config")

    config = configparser.ConfigParser()
    config.read(f"{__file__}\\..\\config.ini")


    REQUIRED = config['GENERAL']['MODULES'].split(', ') + []
    utils.check_modules(REQUIRED)


    with open(f"{__file__}\\..\\lp.csv", "r") as f:
        VALIDLP = (i.strip() for i in f.readlines())

    logger.info("Starting main process")


import worker
import camera
import gui


class taskDistributor:
    def __init__(self, logger=logging.getLogger(__name__), outputQueue=mp.Queue(), inputQueue=mp.Queue(200)):
        self.config = config
        self.logger = logger
        self.loggerQueue = mp.Queue()
        self.outQ = outputQueue
        self.inQ = inputQueue

        self.guiQueue = mp.Queue()
        self.gui = mp.Process(target=gui.GUImgr, args=(self.guiQueue,))
        self.gui.start()

        self.logger.addHandler(QueueHandler(self.guiQueue))

        # add logging from worker and camera processes
        self.loggerQueueListener = QueueListener(self.loggerQueue, *self.logger.handlers)
        self.loggerQueueListener.start()


        self.workers = [workerHandler(i, outputQueue=self.outQ, loggerQueue=self.loggerQueue) for i in range(int(config['GENERAL']['NUM_WORKERS']))]

        self.cameras = [CameraHandler(i, (config[f'CAM_{i}']['IP'], int(config[f'CAM_{i}']['PORT'])), self.inQ, loggerQueue=self.loggerQueue) for i in range(int(config['GENERAL']['NUM_CAMERAS']))]

        self.logger.info(f"Created {len(self.workers)} worker(s) with {len(self.cameras)} camera(s) as inputs")
        self.logger.info("Starting main loop")

    def distribute(self):
        if self.gui.exitcode is not None:
            self.logger.info("GUI closed, exiting")
            self.__del__()
            exit(0)
        for worker in self.workers:
            worker.update()
            if not worker.busy and self.inQ.qsize():
                worker.assignTask(self.inQ.get(block=True))

    def check(self, task:utils.Task):
        cv2.imshow(f"LP: {task.data}", task.img[task.y:task.y+task.h, task.x:task.x+task.w])
        cv2.waitKey(0)
        if task.data not in VALIDLP:
            return
        self.logger.info(f"Found valid LP: {task.data}")

    def __del__(self):
        self.gui.kill()
        for worker in self.workers:
            try:
                worker.kill()
            except:
                pass
        for cam in self.cameras:
            try:
                cam.kill()
            except:
                pass


class CameraHandler:
    def __init__(self, id=-1, addr=("127.0.0.1", 80), inputQueue:mp.Queue=mp.Queue(), loggerQueue=mp.Queue()):
        self._process = mp.Process(target=camera.Camera, args=(id, addr, inputQueue, loggerQueue, True, config[f'CAM_{id}']['LOGIN'], config[f'CAM_{id}']['PASSWORD']))
        self._process.start()
        self._id = id

    def kill(self):
        self._process.terminate()


class workerHandler:
    def __init__(self, id=-1, callback=lambda *_:None, outputQueue:mp.Queue=mp.Queue(), loggerQueue=mp.Queue()):
        self.logger = logging.getLogger(__name__)
        self._Qsend, self._Qrecv = mp.Queue(), mp.Queue()
        self._process = mp.Process(target=worker.Worker, args=(self._Qsend, self._Qrecv, loggerQueue), kwargs={"autostart":True})
        self._process.start()
        self._id = id
        self.busy = False
        self.callback = callback
        self.outputQueue = outputQueue

    def assignTask(self, task:utils.Task):
        self.logger.debug(f"Assigning task {task} to worker {self._id}")
        self.busy = True
        self._Qsend.put(task, block=False)

    def update(self):
        if self._Qrecv.qsize() == 0: return
        taskdone = self._Qrecv.get()
        self.logger.debug(f"Worker {self._id} finished task {taskdone}")
        self.busy = False
        self.outputQueue.put(taskdone)
        self.callback()

    def kill(self):
        self._process.kill()

    def __delete__(self):
        self.kill()


if __name__ == "__main__":
    t = taskDistributor(logger)
    logger.info("Main process startup complete.")
    try:
        while True:
            if not t.outQ.empty() and t.outQ.qsize():
                t.check(t.outQ.get(block=True))
            t.distribute()
    except KeyboardInterrupt:
        logger.info("Main process shutdown.")
        exit()
