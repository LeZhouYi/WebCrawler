import logging
import os
import time
from datetime import datetime

from core.config.config import get_config

logger = logging.getLogger()
logger.setLevel(get_config("logger_level"))

logger_file = "%s\log_%s.log" % (get_config("logger_path"), int(time.time()))

handler = logging.FileHandler(logger_file, encoding="utf-8")
handler.setLevel(get_config("logger_level"))

formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)
