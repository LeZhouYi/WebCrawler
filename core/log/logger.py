import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from core.config.config import get_config_by_section

logger_save_path = get_config_by_section("logger", "save_path")
os.makedirs(logger_save_path, exist_ok=True)
logger_file = "%s/log.log" % logger_save_path

logging.basicConfig(
    level=get_config_by_section("logger", "level"),
    format=get_config_by_section("logger", "format"),
    handlers=[
        TimedRotatingFileHandler(
            filename=logger_file,
            when=get_config_by_section("logger", "when"),
            interval=get_config_by_section("logger", "interval"),
            backupCount=get_config_by_section("logger", "backup_count"),
            encoding=get_config_by_section("logger", "encoding"),
            delay=get_config_by_section("logger", "delay"),
            utc=get_config_by_section("logger", "utc")
        ),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("selenium")