import logging
import os
from datetime import datetime

from core.config.config import get_config

logger = logging.getLogger()
logger.setLevel(get_config("logger_level"))

now_date = datetime.now().strftime("%Y%m%d")
logger_file = "%s_%s.log" % (get_config("logger_file")[:-4], now_date)

handler = logging.FileHandler(logger_file, encoding="utf-8")
handler.setLevel(get_config("logger_level"))

formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)
