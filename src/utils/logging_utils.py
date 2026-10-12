import logging
from . import paths_utils as paths

LOG_DIR = paths.get_resource_path("logs")

logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)  # INFO 级别，ERROR 自然也能记录
logger.propagate = False

if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler(f"{LOG_DIR}/program.log", encoding='utf-8')
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

def loggings_info(text):
    logger.info(text)

def loggings_error(text):
    logger.error(text)