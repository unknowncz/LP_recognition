import multiprocessing as mp
import logging
import os
from sys import stdout
from . import *

SELFDIR = os.path.dirname(os.path.abspath(__file__))

logger = mp.get_logger()
logger.addHandler(logging.StreamHandler(stdout))
logger.setLevel(logging.INFO)