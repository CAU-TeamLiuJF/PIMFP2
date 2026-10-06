import logging.config

from .request_context_filter import RequestContextFilter

LOGGER = logging.getLogger(__name__)


def init_logger(config):
    """
    Configures the logging for the application based on the specified config.
    """
    logging.config.dictConfig(config)
    LOGGER.info(f"logging config: {config}")


def get_logger(name):
    """
     Get a logger with the specified name.
    """
    return logging.getLogger(name)


__all__ = [
    "init_logger",
    "get_logger",
    "RequestContextFilter"
]
