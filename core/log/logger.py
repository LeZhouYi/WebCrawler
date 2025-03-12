import logging
import os
import time

from core.config.config import get_config_by_section

logger = logging.getLogger()
logger_level = get_config_by_section("logger","level")
logger.setLevel(logger_level)

logger_save_path = get_config_by_section("logger","save_path")
os.makedirs(logger_save_path, exist_ok=True)
logger_file = "%s\\log_%s.log" % (logger_save_path, int(time.time()))

handler = logging.FileHandler(logger_file, encoding="utf-8")
handler.setLevel(logger_level)

formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)
