from enum import IntEnum
from functools import partial
import logging

from titan.qt import QtCore, QtWidgets
from .filters import TextFilter, DropDownFilter


# Headers for the table view
class Headers(IntEnum):

    def __new__(cls, value, label):
        obj = int.__new__(cls, value)
        obj._value_ = value
        setattr(obj, "label", label)
        return obj

    Time = (0, "Time")
    Level = (1, "Level")
    Name = (2, "Name")
    Message = (3, "Message")


# Filters for the table view
Filters = {
    Headers.Time: TextFilter,
    Headers.Level: DropDownFilter,
    Headers.Name: TextFilter,
    Headers.Message: TextFilter,
}


# Log levels
class Levels(IntEnum):

    def __new__(cls, level_num, level_name):
        obj = int.__new__(cls, level_num)
        obj._value_ = level_num
        setattr(obj, "level_name", level_name)
        return obj

    Any = (9999, "ANY")
    Trace = (logging.TRACE, "TRACE")
    Debug = (logging.DEBUG, "DEBUG")
    Info = (logging.INFO, "INFO")
    Warning = (logging.WARNING, "WARNING")
    Error = (logging.ERROR, "ERROR")
    Critical = (logging.CRITICAL, "CRITICAL")


def split_seq(value: str) -> tuple[str]:
    """Splits comma-separated values into a sequence."""
    values = (x.strip() for x in value.split(","))
    return tuple(x for x in values if x)


class TitanLoggerFilterHeaderView(QtWidgets.QHeaderView):
    """A HeaderView that provides a persistent filter field for use with the
    ProxyModel."""

    filter_changed = QtCore.Signal(int, list)

    def __init__(
        self, orientation: QtCore.Qt.Orientation, parent: QtWidgets.QWidget
    ) -> None:
        super().__init__(orientation, parent)
        self._filters = []
        self._padding = 2
        self.setStretchLastSection(True)
        self.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.setSortIndicatorShown(False)
        self.setSectionsMovable(True)
        self.sectionResized.connect(self.adjust_positions)
        parent.horizontalScrollBar().valueChanged.connect(self.adjust_positions)

    def sizeHint(self) -> int:
        """Returns the size hint for the header view."""
        size = super().sizeHint()
        if self._filters:
            height = self._filters[0].sizeHint().height()
            size.setHeight(size.height() + height + self._padding * 2)
        return size

    def updateGeometries(self) -> None:
        """Updates the geometries of the header view."""
        if self._filters:
            height = self._filters[0].sizeHint().height()
            self.setViewportMargins(0, self._padding, 0, height + self._padding)
        else:
            self.setViewportMargins(0, 0, 0, 0)
        super().updateGeometries()
        self.adjust_positions()

    def adjust_positions(self) -> None:
        """Adjusts the positions of the filters widgets."""
        for index, filter in enumerate(self._filters):
            height = filter.sizeHint().height()
            x = self.sectionPosition(index) - self.offset() + 2
            y = height + (self._padding * 2) + 1
            filter.move(x, y)
            filter.resize(self.sectionSize(index), height)

    def add_filter(self, log_filter: QtCore.QObject) -> None:
        """Adds a filter to the header view."""
        cur_index = len(self._filters)
        self._filters.append(log_filter)
        log_filter.filter_changed.connect(partial(self._on_filter_changed, cur_index))

    def get_filter(self, index):
        """Returns the filter at the given index."""
        return self._filters[index]

    @QtCore.Slot(int, str)
    def _on_filter_changed(self, index: int, text: str) -> None:
        """Emits the filter changed signal."""
        values = split_seq(text)
        self.filter_changed.emit(index, values)

    def reset_filters(self) -> None:
        """Resets all the filters."""
        for filter in self._filters:
            filter.reset_filter()
