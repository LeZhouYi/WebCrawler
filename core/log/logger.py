import logging
import os
import sys
import time

from core.config.config import get_config_by_section

logger_save_path = get_config_by_section("logger","save_path")
os.makedirs(logger_save_path, exist_ok=True)
logger_file = "%s/log_%s.log" % (logger_save_path, int(time.time()))

logging.basicConfig(
    level=get_config_by_section("logger","level"),
    format='%(asctime)s-%(name)s-%(levelname)s-%(message)s',
    handlers=[
        logging.FileHandler(logger_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("selenium")
