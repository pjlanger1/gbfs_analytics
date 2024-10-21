# utils.py

# standard library
from logging import basicConfig, getLogger, INFO, Logger


def get_logger() -> Logger:
    basicConfig(level=INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = getLogger(__name__)
    return logger
