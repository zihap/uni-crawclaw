import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger('server')


def log_debug(message: str):
    logger.debug(message, stacklevel=2)


def log_info(message: str):
    logger.info(message, stacklevel=2)


def log_warning(message: str):
    logger.warning(message, stacklevel=2)


def log_error(message: str):
    logger.error(message, stacklevel=2)
