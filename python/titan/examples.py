from titan.host.maya import Maya
from titan.logger import get_logger


class ExampleCallback:
    """Example of a callback that listens for selection changes in Maya.

    >>> from titan.examples import ExampleCallback
    >>> example = ExampleCallback(
    >>> # This logs selection changes in Maya
    >>> del example
    >>> # The callback is no longer active, the registered callback is removed
    >>> # and will be logged.
    """

    def __init__(self):
        self._callback_id = Maya.event_manager.register_callback(
            Maya.events.SelectionChanged, self.selection_changed
        )

    def selection_changed(self):
        logger = get_logger("titan.examples")
        logger.info(Maya.cmds.ls(sl=True))


def raise_exception():
    """Raise a test exception and log it."""
    try:
        raise ValueError("This is a test exception")
    except ValueError:
        logger = get_logger("titan.examples")
        logger.exception("This is a test exception")
