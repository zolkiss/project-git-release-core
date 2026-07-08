import logging


def create_logger(name: str,
                  level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


def create_console_handler(level: int = logging.INFO,
                           log_format: str = '%(asctime)s - %(levelname)s: %(message)s') -> logging.StreamHandler:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))
    return console_handler


log = create_logger(name=__name__, level=logging.DEBUG)

log.addHandler(create_console_handler(level=logging.DEBUG))

from project_git_release.core import Connector, ReleaseEngine

__all__ = ["Connector", "ReleaseEngine", "log", "create_logger", "create_console_handler"]
