import multiprocessing as mp
import time
import os

import worker


import random
import cv2

class taskDistributor:
    def __init__(self, worker_count=1, taskList:list=None, outputQueue=mp.Queue(), backlog=25):
        self.out = outputQueue
        self.taskList = taskList or []
        self.workers = tuple(workerHandler(i, self.distribute, self.out) for i in range(worker_count))
        print(f"Created {len(self.workers)} workers")
        self.backlog = backlog

    def addTask(self, task):
        added = False
        if len(self.taskList) < self.backlog:
            self.taskList.append(task)
            added = True
        self.distribute()
        return added

    def distribute(self):
        for worker in self.workers:
            worker.update()
            if not worker.busy and len(self.taskList) > 0:
                worker.assignTask(self.taskList.pop(0))

    def __del__(self):
        for worker in self.workers:
            worker.kill()


class workerHandler:
    def __init__(self, id=-1, callback=lambda *_:None, outputQueue:mp.Queue=mp.Queue()):
        self._Qsend, self._Qrecv = mp.Queue(), mp.Queue()
        self._process = mp.Process(target=worker.Worker, args=(self._Qsend, self._Qrecv), kwargs={"autostart":True})
        self._process.start()
        self._id = id
        self.busy = False
        self.callback = callback
        self.outputQueue = outputQueue

    def assignTask(self, task:worker.Task):
        self.busy = True
        self._Qsend.put(task, block=False)

    def update(self):
        if self._Qrecv.qsize() == 0: return
        taskdone = self._Qrecv.get()
        self.busy = False
        self.outputQueue.put(taskdone)
        self.callback()

    def get_id(self):
        return self._id

    def kill(self):
        self._process.kill()

    def __delete__(self):
        self.kill()


if __name__ == "__main__":
    t = taskDistributor(1)
    files = [f for f in os.listdir(f"{__file__}\\..\\LP_Detection\\train")]
    print(len(files))
    # im = cv2.imread(f"{__file__}\\..\\LP_Detection\\train\\000f52302c1341eb_jpg.rf.aee8f06b336f83868708a3591d4100b4.jpg")
    i = 0
    print(len(files))
    while True:
        if not files[i].endswith(".jpg"):
            i+1
            continue
        im = cv2.imread(f"{__file__}\\..\\LP_Detection\\train\\{files[i]}")
        if t.addTask(worker.Task(i, im)):
            print(f"Added task {i}")
            i += 1
            if i >= len(files)-2: break
        del im
        t.distribute()
    while True:
        if t.out.qsize():
            print(t.out.get())
