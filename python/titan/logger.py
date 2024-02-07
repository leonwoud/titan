import os
import logging
import tempfile

LOG_FILENAME = os.path.join(tempfile.gettempdir(), "titan.log")


def get_logger(name):

    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create a file handler
    handler = logging.FileHandler(LOG_FILENAME)
    handler.setLevel(logging.DEBUG)

    # create a logging format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)

    return logger
