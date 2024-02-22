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
#  - fix manual override (broken due to pickeling of entire taskManager object not being possible anymore, at least on windows?)
#  - above fixed?
#  - update todo regularly

logger = mp.get_logger()
logger.addHandler(logging.StreamHandler(stdout))
if __name__ == "__main__":
    # logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s")

    logger.addHandler(logging.FileHandler(f"{SELFDIR}/log", mode='w'))
    logger.setLevel(logging.INFO)


from . import utils, worker, camera, gui, dbmgr


class taskDistributor:
    """Main class for the ANPR system. Will handle the camera and worker processes, as well as the GUI and the communication between the parts.
    """
    def __init__(self, logger=logging.getLogger(), outputQueue=None, inputQueue=None, successCallback=lambda *_:None):
        """Initialize the task distributor

        Args:
            logger (logging.Logger, optional): Logger to use. Defaults to logging.getLogger().
            outputQueue (Namespace, optional): Will contain the worker output tasks as attributes in the following format "wkr_id{camera_id}". Creates Namespace if one is not provided.
            inputQueue (Namespace, optional): Will contain the camera input tasks as attributes in the following format "cam_id{camera_id}". Creates Namespace if one is not provided.
        """
        self.config = config
        self.logger = logger
        self.loggerQueue = mp.Queue()

        self.mpmanager = mp.Manager()
        if inputQueue is None:
            self.inQ = self.mpmanager.Namespace()
        else:
            self.inQ = inputQueue
        self.inQ_nextidx = 0
        for i in range(int(config['GENERAL']['NUM_CAMERAS'])):
            self.inQ.__setattr__(f"cam_id{i}", [])

        if outputQueue is None:
            if inputQueue is None:
                self.outQ = self.inQ
            else:
                self.outQ = self.mpmanager.Namespace()
        else:
            self.outQ = outputQueue

        for i in range(int(config['GENERAL']['NUM_WORKERS'])):
            self.outQ.__setattr__(f"wkr_id{i}", None)

        self.nextautopass = mp.Queue()
        self.dbmgr = dbmgr.DatabaseHandler(f"{SELFDIR}/lp.csv", logger=self.logger, overridedb=self.mpmanager.dict())
        self.successCallback = successCallback

        self.guiQueue = mp.Queue()
        self.gui = mp.Process(target=gui.GUImgr, args=(self.guiQueue, self.dbmgr, self.nextautopass))
        self.gui.start()

        self.logger.addHandler(QueueHandler(self.guiQueue))

        # add logging from worker and camera processes
        self.loggerQueueListener = QueueListener(self.loggerQueue, *self.logger.handlers)
        self.loggerQueueListener.start()

        # determine which model type to use
        if config['GENERAL']['MODEL_TYPE'] in ['lite', 'tf']:
            model_type = config['GENERAL']['MODEL_TYPE']

        # start the worker and camera processes
        self.workers = [workerHandler(i, output=self.outQ, loggerQueue=self.loggerQueue, model_type=model_type) for i in range(int(config['GENERAL']['NUM_WORKERS']))]
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
        frame = getattr(self.inQ, f"cam_id{self.inQ_nextidx}")
        if frame == []:
            sleep(0.01)
            return
        for worker in self.workers:
            worker.update()
            if not worker.busy:
                worker.assignTask(frame)
                self.inQ.__setattr__(f"cam_id{self.inQ_nextidx}", [])
                self.inQ_nextidx = (self.inQ_nextidx + 1) % int(config['GENERAL']['NUM_CAMERAS'])

    def check(self, task:utils.Task):
        """Will check if the task is valid and should be processed

        Args:
            task (utils.Task): Task to check in format (bbox, (lp, conf))

        Returns:
            Bool: Success
        """
        success = False
        # check if the manual override is active, if so, the check passes automatically
        try:
            nextpass = self.nextautopass.get_nowait()
        except:
            nextpass = 0
        if time() < nextpass:
            self.logger.info(f"Manual override trigerred")
            success = True
        else:
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
            if (valid := next((entry for entry in self.dbmgr if entry[0] in lp), None)) != None:
            # if any([dbentry[0] in lp for dbentry in self.dbmgr]):
            # if lp in self.dbmgr:
            # if True:
                success = True

        if success:
            self.logger.info(f"Found valid LP: {valid[0]}; {valid[1]}")
            # send callback
            self.successCallback()

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
    def __init__(self, id:int, inputQ, loggerQueue=mp.Queue()):
        """Initialize the camera handler and start the camera process

        Args:
            id (int): Camera process ID. Defaults to -1.
            inputQ (Namespace, optional): Collected frames will be put here in the utils.task form.
            loggerQueue (mp.Queue, optional): Queue for logging connections. Defaults to mp.Queue().
        """
        # start the camera process
        cfg = {"protocol":"rtsp", "port":554, "login":"admin", "password":"admin", "ip":"127.0.0.1", "id":id}
        cfg |= {k:v for k,v in config[f'CAM_{id}'].items()}
        self._process = mp.Process(target=camera.Camera, args=(cfg, inputQ, loggerQueue, True), name=f"Camera_{id}_process")
        self._process.start()
        self.cfg = cfg

    def kill(self):
        self._process.kill()

class workerHandler:
    """Wrapper class for the worker process for easier management
    """
    def __init__(self, id:int, output, callback=lambda *_:None, loggerQueue=mp.Queue(), model_type='tf'):
        """Initialize the worker handler and start the worker process

        Args:
            id (int, optional): Worker ID. Defaults to -1.
            output (Namespace): Namespace for outputting finished tasks.
            callback (function, optional): Callback on successful return from task. Defaults to lambda*_:None.
            loggerQueue (mp.Queue, optional): Queue for logging connections. Defaults to mp.Queue().
            model_type (str, optional): Model type to use. Defaults to 'tf'.
        """
        self.logger = logging.getLogger(__name__)
        # setup communication queues
        self._Qsend, self._Qrecv = mp.Queue(), mp.Queue()
        # start the worker process
        self._process = mp.Process(target=worker.Worker, args=(self._Qsend, self._Qrecv, loggerQueue), kwargs={"autostart":True, "model_type":model_type}, name=f"Worker_{id}_process")
        self._process.start()
        self._id = id
        self.busy = False
        self.callback = callback
        self.output = output

    def assignTask(self, task:utils.Task):
        """Assign a task to the worker process

        Args:
            task (utils.Task): Task to assign to the worker.
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
        self.busy = False
        taskdone = self._Qrecv.get()
        self.output.__setattr__(f"wkr_id{self._id}", taskdone)
        self.logger.debug(f"Worker {self._id} finished task {taskdone.id}")
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
    nextcheck = 0
    try:
        while True:
            f = t.outQ.__getattr__(f"wkr_id{nextcheck}")
            t.outQ.__setattr__(f"wkr_id{nextcheck}", None)
            if not f is None:
                t.check(f)
            else:
                sleep(0.05)
            nextcheck = (nextcheck + 1) % int(config['GENERAL']['NUM_WORKERS'])
            t.distribute()
    except KeyboardInterrupt:
        logger.info("Main process shutdown.")
        exit()
