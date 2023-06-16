import multiprocessing as mp
from sys import stdout
from configparser import ConfigParser
import logging
from logging.handlers import QueueHandler, QueueListener
from time import time, sleep
import os
if __name__ == "__main__":
    mp.set_start_method('fork') if os.name == 'posix' else mp.set_start_method('spawn')

SELFDIR = os.path.abspath(f'{__file__}/..')

# TODO:
#  - Logging - finalise logging system (colors, formatting, etc.)

logger = mp.get_logger()
logger.addHandler(logging.StreamHandler(stdout))
if __name__ == "__main__":
    # logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s")

    logger.addHandler(logging.FileHandler(f"{SELFDIR}/log", mode='w'))
    logger.setLevel(logging.INFO)


import utils

import worker
import camera
import gui
import dbmgr


class taskDistributor:
    """Main class for the ANPR system. Will handle the camera and worker processes, as well as the GUI and the communication between the parts.
    """
    def __init__(self, logger=logging.getLogger(), outputQueue=mp.Queue(), inputQueue=mp.Queue(200)):
        """Initialise the task distributor

        Args:
            logger (logging.Logger, optional): Logger to use. Defaults to logging.getLogger(__name__).
            outputQueue (mp.Queue, optional): dWill contain the worker output tasks. Defaults to mp.Queue().
            inputQueue (mp.Queue, optional): Will contain the camera input tasks. Always limit the size when changing from default. Defaults to mp.Queue(200).
        """
        self.config = config
        self.logger = logger
        self.loggerQueue = mp.Queue()
        self.outQ = outputQueue
        self.inQ = inputQueue
        self.dbmgr = dbmgr.DatabaseHandler(f"{SELFDIR}/lp.csv", logger=self.logger)
        self.nextautopass = (time(), False)

        self.guiQueue = mp.Queue()
        self.gui = mp.Process(target=gui.GUImgr, args=(self.guiQueue, self.dbmgr, self))
        self.gui.start()

        self.logger.addHandler(QueueHandler(self.guiQueue))

        # add logging from worker and camera processes
        self.loggerQueueListener = QueueListener(self.loggerQueue, *self.logger.handlers)
        self.loggerQueueListener.start()


        self.workers = [workerHandler(i, outputQueue=self.outQ, loggerQueue=self.loggerQueue) for i in range(int(config['GENERAL']['NUM_WORKERS']))]

        self.cameras = [CameraHandler(i, self.inQ, loggerQueue=self.loggerQueue) for i in range(int(config['GENERAL']['NUM_CAMERAS']))]

        self.logger.info(f"Created {len(self.workers)} worker(s) with {len(self.cameras)} camera(s) as inputs")
        self.logger.info("Starting main loop")

    def distribute(self):
        """Will check for new tasks and assign them to workers. Needs to be called in a loop.
        """
        if self.gui.exitcode is not None:
            self.logger.info("GUI closed, exiting")
            self.kill()
            exit(0)
        for worker in self.workers:
            worker.update()
            if not worker.busy and self.inQ.qsize():
                worker.assignTask(self.inQ.get())

    def check(self, task:utils.Task):
        """Will check if the task is valid and should be processed

        Args:
            task (utils.Task): Task to check in format (bbox, (lp, conf))

        Returns:
            Bool: Success
        """
        # check if the manual override is active, if so, the check passes automatically
        if self.nextautopass[1] and time() < self.nextautopass[0]:
            self.logger.info(f"Manual override trigerred")
            self.nextautopass = (time(), False)
            return True
        # check if the task is valid
        if len(task.data) == 0: return

        if len(task.data) >= 2:
            joinedtask = utils.joinpredictions(task)
        else:
            joinedtask = utils.Task(task.id, task.data[0])
        if len(joinedtask.data[1]) != 2: return
        # unpack the task data
        bbox, (lp, conf) = joinedtask.data
        # check if the LP is in the database
        self.logger.info(f"Checking LP: {lp}")
        if lp in self.dbmgr:
        # if True:
            self.logger.info(f"Found valid LP: {lp}; {self.dbmgr[lp]}")
            print(lp)
            return True

    def kill(self):
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
    """Wrapper class for the camera process for easier management
    """
    def __init__(self, id=-1, inputQueue:mp.Queue=mp.Queue(), loggerQueue=mp.Queue()):
        """Initialise the camera handler and start the camera process

        Args:
            id (int, optional): Camera process ID. Defaults to -1.
            inputQueue (mp.Queue, optional): Collected frames will be put here in the utils.task form. Defaults to mp.Queue().
            loggerQueue (mp.Queue, optional): Queue for logging connections. Defaults to mp.Queue().
        """
        # start the camera process
        cfg = {k:v for k,v in config[f'CAM_{id}'].items()}
        cfg |= {"id":id}
        self._process = mp.Process(target=camera.Camera, args=(cfg, inputQueue, loggerQueue, True), name=f"Camera_{id}_process")
        self._process.start()
        self.cfg = cfg

    def kill(self):
        self._process.kill()

class workerHandler:
    """Wrapper class for the worker process for easier management
    """
    def __init__(self, id=-1, callback=lambda *_:None, outputQueue:mp.Queue=mp.Queue(), loggerQueue=mp.Queue()):
        """Initialise the worker handler and start the worker process

        Args:
            id (int, optional): Worker ID. Defaults to -1.
            callback (function, optional): Callback on successful return from task. Defaults to lambda*_:None.
            outputQueue (mp.Queue, optional): Queue for outputting finished tasks. Defaults to mp.Queue().
            loggerQueue (mp.Queue, optional): Queue for logging connections. Defaults to mp.Queue().
        """
        self.logger = logging.getLogger(__name__)
        # setup communication queues
        self._Qsend, self._Qrecv = mp.Queue(), mp.Queue()
        # start the worker process
        self._process = mp.Process(target=worker.Worker, args=(self._Qsend, self._Qrecv, loggerQueue), kwargs={"autostart":True}, name=f"Worker_{id}_process")
        self._process.start()
        self._id = id
        self.busy = False
        self.callback = callback
        self.outputQueue = outputQueue

    def assignTask(self, task:utils.Task):
        """Assign a task to the worker process

        Args:
            task (utils.Task): Task to assign in format (bbox, (lp, conf))
        """
        # assign a task to the worker process and mark it as busy
        self.logger.debug(f"Assigning task {task} to worker {self._id}")
        self.busy = True
        self._Qsend.put(task, block=False)

    def update(self):
        """Check if the worker has finished a task and put it in the output queue
        """
        # check if the worker has finished a task, if so, mark it as not busy and put the task in the output queue
        if self._Qrecv.qsize() == 0: return
        taskdone = self._Qrecv.get()
        self.logger.debug(f"Worker {self._id} finished task {taskdone}")
        self.busy = False
        self.outputQueue.put(taskdone)
        self.callback()

    def kill(self):
        """Kill the worker process
        """
        self._process.kill()

    def __del__(self):
        self.kill()


if __name__ == "__main__":
    config = ConfigParser()
    config.read(f"{SELFDIR}/config.ini")
    t = taskDistributor(logger)
    logger.info("Main process startup complete.")
    try:
        while True:
            if not t.outQ.empty():
                t.check(t.outQ.get(block=True))
            else:
                sleep(0.05)
            t.distribute()
    except KeyboardInterrupt:
        logger.info("Main process shutdown.")
        exit()
