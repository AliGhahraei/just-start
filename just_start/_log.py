from logging import getLogger, FileHandler, Formatter
from os import makedirs

from .constants import LOG_PATH, LOCAL_DIR

log = getLogger('just_start')

makedirs(LOCAL_DIR, exist_ok=True)
_file_handler = FileHandler(LOG_PATH)
_file_handler.setFormatter(Formatter('%(asctime)s\n%(message)s'))
log.addHandler(_file_handler)
