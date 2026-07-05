import logging
from logging import StreamHandler, Logger


def create_logger(name: str,
                  level: int = logging.INFO) -> Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


def create_console_handler(level: int = logging.INFO,
                           log_format: str = '%(asctime)s - %(levelname)s: %(message)s') -> StreamHandler:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))
    return console_handler
