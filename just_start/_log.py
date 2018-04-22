from logging import getLogger, FileHandler, Formatter

from .constants import LOG_PATH

log = getLogger('just_start')

_file_handler = FileHandler(LOG_PATH)
_file_handler.setFormatter(Formatter('%(asctime)s\n%(message)s'))
log.addHandler(_file_handler)
