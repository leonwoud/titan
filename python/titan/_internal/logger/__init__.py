from __future__ import absolute_import

import logging
from typing import Any, Mapping, Optional, Tuple

TRACE_LEVEL = logging.DEBUG - 5


class TitanLogger(logging.getLoggerClass()):

    def __init__(self, name: str, level: Optional[int] = logging.NOTSET) -> None:
        super(TitanLogger, self).__init__(name, level)
        logging.addLevelName(TRACE_LEVEL, "TRACE")

    def trace(
        self, msg: str, *args: Tuple[Any, ...], **kwargs: Mapping[str, Any]
    ) -> None:
        if self.isEnabledFor(TRACE_LEVEL):
            self._log(TRACE_LEVEL, msg, args, **kwargs)


logging.setLoggerClass(TitanLogger)
setattr(logging, "TRACE", TRACE_LEVEL)
