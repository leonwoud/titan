"""
Using the Titan Logger
======================
The Titan logger is a simple wrapper around the Python logging module. It provides a way to create loggers with a
consistent format and level.

It is recommended not to store loggers at the module scope, but instead to create them as needed. This will allow
the global log level and log propogation to be changed at runtime. Calling `get_logger` with the same name will
return the same logger, as stored by the logging module.

Creating a Logger
=================

To create a logger, use the `get_logger` function. This function will return a logger with the given name. If the
logger already exists, it will return the existing logger.

Example:

    >>> from titan.logger import get_logger
    >>> logger = get_logger("titan.example")

The logger can then be used to log messages at different levels.

Logging timed function calls
============================

Exception Handling
==================
When an exception is raised, the logger can be used to log the exception and the stack trace. This is done using the
`exception` method.

This is recommended over using the `error` method, as the `exception` method will log the stack trace as well as the
message and will be available via the GUI logger. The message will be logged, and the stack trace will be available
via the GUI logger.

Example:

    >>> from titan.logger import get_logger
    >>> def some_function():
    >>>    logger = get_logger("titan.example")
    >>>    try:
    >>>        1 / 0
    >>>    except ZeroDivisionError:
    >>>        logger.exception("An error occurred")

"""

from datetime import datetime
from functools import wraps
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import tempfile
from typing import Callable, Optional

from titan.qt import is_qt_app
from titan._internal.logger.gui.main import TitanLogHandler, get_logger_model

# Constants
LOG_FILENAME = os.path.join(tempfile.gettempdir(), "titan.log")
DEFAULT_GLOBAL_LOG_LEVEL = logging.DEBUG
PROPOGATE = True


def set_global_log_level(level: int) -> None:
    global DEFAULT_GLOBAL_LOG_LEVEL
    DEFAULT_GLOBAL_LOG_LEVEL = level


def propogate_titan_logs(state: bool) -> None:
    global PROPOGATE
    PROPOGATE = state


def get_logger(name, log_level: Optional[int] = None) -> logging.Logger:
    """Get a logger with a given name. If the logger already exists, return it."""

    if log_level is None:
        log_level = DEFAULT_GLOBAL_LOG_LEVEL

    if name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.propagate = PROPOGATE
        return logger

    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = PROPOGATE

    file_handler = TimedRotatingFileHandler(
        LOG_FILENAME, when="midnight", backupCount=7
    )
    file_handler.setLevel(logging.DEBUG)

    # create a logging format
    file_formatter = logging.Formatter(
        "%(asctime)s : %(levelname)s : %(name)s : %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # add the handlers to the logger
    logger.addHandler(file_handler)

    # Setup the GUI Logger
    if is_qt_app():
        model = get_logger_model()
        gui_handler = TitanLogHandler(model)
        # gui_formatter = logging.Formatter(
        #    "%(asctime)s : %(levelname)s : %(name)s : %(message)s"
        # )
        # gui_handler.setFormatter(gui_formatter)
        logger.addHandler(gui_handler)

    return logger


def log_execution_time(logger_name: str):
    """A decorator to log the execution time of a function"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.now()
            execution_time = end_time - start_time
            logger = get_logger(logger_name)
            logger.log(
                logging.DEBUG,
                "Function %s executed in %s" % (func.__qualname__, execution_time),
            )
            return result

        return wrapper

    return decorator
