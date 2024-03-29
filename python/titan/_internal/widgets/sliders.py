from typing import Optional
from titan.qt import QtCore, QtWidgets


class FloatSlider(QtWidgets.QSlider):
    """A slider that emits float values instead of integers."""

    value_changed = QtCore.Signal(float)

    def __init__(
        self,
        min_val: float,
        max_val: float,
        step: float,
        orientation: Optional[QtCore.Qt.Orientation] = QtCore.Qt.Horizontal,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(orientation=orientation, parent=parent)
        self._min_val = min_val
        self._max_val = max_val
        self._step = step
        self.setRange(0, round((max_val - min_val) / step))
        self.setSingleStep(step)
        self.valueChanged.connect(self._on_slider_changed)

    @QtCore.Slot(int)
    def _on_slider_changed(self, value):
        scaled_value = (value / self.maximum()) * (self._max_val - self._min_val)
        self.value_changed.emit(round(self._min_val + scaled_value, 3))

    def set_value(self, value):
        value = round((value - self.min) / (self.max - self.min) * self.maximum())
        super().setValue(value)

    @property
    def min(self):
        return self._min_val

    @property
    def max(self):
        return self._max_val


class IntSlider(QtWidgets.QSlider):
    """A slider that emits integer values."""

    value_changed = QtCore.Signal(int)

    def __init__(
        self,
        min_val: int,
        max_val: int,
        step: int,
        orientation: Optional[QtCore.Qt.Orientation] = QtCore.Qt.Horizontal,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(orientation=orientation, parent=parent)
        self._min_val = min_val
        self._max_val = max_val
        self._step = step
        self.setRange(min_val, max_val)
        self.setSingleStep(step)
        self.valueChanged.connect(self._on_slider_changed)

    @QtCore.Slot(int)
    def _on_slider_changed(self, value):
        self.value_changed.emit(value)

    def set_value(self, value):
        super().setValue(value)

    @property
    def min(self):
        return self._min_val

    @property
    def max(self):
        return self._max_val
