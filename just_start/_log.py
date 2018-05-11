from logging import getLogger, FileHandler, Formatter
from os import makedirs

from .constants import LOG_PATH, LOCAL_DIR

makedirs(LOCAL_DIR, exist_ok=True)

log = getLogger('just_start')

_file_handler = FileHandler(LOG_PATH)
_file_handler.setFormatter(Formatter('%(asctime)s| %(levelname)s| %(module)s@%(lineno)d'
                                     '\n%(message)s'))
log.addHandler(_file_handler)
