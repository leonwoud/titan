from typing import Optional

from titan.qt import QtCore, QtWidgets


class HeaderFilter(QtCore.QObject):
    """Base class for filters"""

    filter_changed = QtCore.Signal(str)

    def reset_filter(self) -> None:
        """Abstract method called when subclassed filters should be reset."""
        raise NotImplementedError()


class TextFilter(QtWidgets.QLineEdit, HeaderFilter):
    """A filter that allows the user to type in a string to filter the model."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super(TextFilter, self).__init__(parent=parent)
        self.setPlaceholderText("Filter")
        self.setClearButtonEnabled(True)
        self.textChanged.connect(self.filter_changed.emit)

    def reset_filter(self) -> None:
        """Clear the filter."""
        self.clear()


class DropDownFilter(QtWidgets.QComboBox, HeaderFilter):
    """A filter that allows the user to select a value from a drop down to filter the model."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super(DropDownFilter, self).__init__(parent=parent)
        self.currentIndexChanged.connect(self._on_index_changed)

    @QtCore.Slot(int)
    def _on_index_changed(self, index: int) -> None:
        data = self.itemData(index)
        self.filter_changed.emit(data)

    def reset_filter(self) -> None:
        self.setCurrentIndex(0)
