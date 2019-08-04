from logging import getLogger, FileHandler, Formatter
from os import makedirs

from .constants import LOG_PATH, LOCAL_DIR

makedirs(LOCAL_DIR, exist_ok=True)

logger = getLogger()

file_handler = FileHandler(LOG_PATH)
file_handler.setFormatter(Formatter('%(asctime)s| %(levelname)s| %(module)s@%(lineno)d'
                                    '\n%(message)s'))
logger.addHandler(file_handler)
