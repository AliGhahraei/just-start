from logging import getLogger, FileHandler, Formatter
from os import makedirs

from .constants import LOG_PATH, LOCAL_DIR

logger = getLogger('just_start')
try:
    _file_handler = FileHandler(LOG_PATH)
except FileNotFoundError:
    makedirs(LOCAL_DIR)
    _file_handler = FileHandler(LOG_PATH)

logger.addHandler(_file_handler)
_file_handler.setFormatter(Formatter('%(asctime)s\n%(message)s'))
