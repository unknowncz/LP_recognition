import multiprocessing as mp
import logging
import os
from sys import stdout

SELFDIR = os.path.dirname(os.path.abspath(__file__))

logger = mp.get_logger()
formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
streamhandler = logging.StreamHandler(stdout)
streamhandler.setFormatter(formatter)
logger.addHandler(streamhandler)

# race condition with logger when writing to file TODO: fix (critical)
filehandler = logging.FileHandler(os.path.join(SELFDIR, 'log'), mode='w')
filehandler.setFormatter(formatter)
logger.addHandler(filehandler)
logger.setLevel(logging.INFO)

from . import *
