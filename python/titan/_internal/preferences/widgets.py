from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

from titan.qt import QtCore, QtGui, QtWidgets
from titan.widgets import (
    ColorPicker as _ColorPicker,
    FloatSlider,
    IntSlider,
)

from titan._internal.preferences.components import Component, DataTypes, Number


@contextmanager
def block_signals(widget: QtWidgets.QWidget):
    """Block signals for a widget."""
    widget.blockSignals(True)
    yield
    widget.blockSignals(False)


class PreferenceBase(QtCore.QObject):
    """Base class for preference widgets.

    This class provides a common interface for preference widgets to be used in the preferences
    dialog. It provides a way to get and set values from the preferences and a way to reset the
    values to their defaults.
    """

    value_changed = QtCore.Signal(object)

    def __init__(self):
        super().__init__()
        self._component = None
        self._default = None

    @classmethod
    def from_component(cls, component: Component):
        """Create a preference widget from a component."""
        raise NotImplementedError

    def set_component(self, component: Component):
        """Set the component for this preference widget."""
        self._component = component

    def get_value(self):
        """Get the value from the widget."""
        raise NotImplementedError

    def set_value(self, value):
        """Records the value in the preferences."""
        if self._component:
            print(f"Setting value for {self._component.path} to {value}")
            self._component.preferences.set_value(self._component.path, value)
        self.value_changed.emit(value)

    def restore_default(self):
        """Reset the widget to its default value."""
        raise NotImplementedError

    def reload(self):
        """Reload the value from the preferences."""
        self.set_value(self._component.value)

    @property
    def default(self):
        return self._default


class CheckBox(QtWidgets.QCheckBox, PreferenceBase):
    """A checkbox preference widget."""

    @classmethod
    def from_component(cls, component: Component):
        inst = cls(component.value, component.default, component.label)
        inst.set_component(component)
        return inst

    def __init__(
        self,
        value: bool,
        default: bool,
        label: Optional[str] = None,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(label, parent=parent)
        self._default = default
        self.setChecked(value)
        self._update_label_font(value)
        self.stateChanged.connect(self._on_state_changed)

    @QtCore.Slot(int)
    def _on_state_changed(self, value: int) -> None:
        value = bool(value)
        super().set_value(value)
        self._update_label_font(value)

    def _update_label_font(self, value: bool) -> None:
        is_default = value == self._default
        font = self.font()
        font.setBold(not is_default)
        font.setItalic(not is_default)
        self.setFont(font)

    def get_value(self) -> bool:
        return self.isChecked()

    def set_value(self, value: bool) -> None:
        self.setChecked(value)
        self._update_label_font(value)

    def restore_default(self) -> None:
        self.set_value(self._default)


class Field(QtWidgets.QLineEdit, PreferenceBase):
    """A Field preference widget.

    This widget is used for entering text values. It can be used for entering strings,
    integers, or floats. The widget will validate the input based on the data type and
    range provided.
    """

    @classmethod
    def from_component(cls, component: Component):
        inst = cls(
            component.data_type,
            component.value,
            component.default,
            range_=component.range,
        )
        inst.set_component(component)
        return inst

    def __init__(
        self,
        data_type: type,
        value: DataTypes,
        default: DataTypes,
        range_: Optional[tuple[Number, Number]] = None,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        self._default = default
        self._range = range_
        self._data_type = data_type
        self._validator = None
        self._component = None
        # Using QRegularExpressionValidator for int and float types
        # instead of QIntValidator and QDoubleValidator.
        if self._data_type in (int, float):
            if self._data_type == float:
                regex = QtCore.QRegularExpression(
                    "^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$"
                )
            elif self._data_type == int:
                regex = QtCore.QRegularExpression("^-?\\d+$")
            self._validator = QtGui.QRegularExpressionValidator(regex, self)
            self.setValidator(self._validator)
        self.setText(str(value))
        self.editingFinished.connect(self._on_editing_finished)

    @QtCore.Slot()
    def _on_editing_finished(self):
        """Checks if the value is within the range and sets it if it is not."""
        value = self.get_value()
        if self._range is not None:
            if value < self._range[0]:
                value = self._range[0]
            elif value > self._range[1]:
                value = self._range[1]
        self.set_value(value)

    def get_value(self):
        return self._data_type(self.text())

    def set_value(self, value: DataTypes):
        """Set the value in the widget."""
        self.setText(str(value))
        super().set_value(value)

    def restore_default(self):
        self.set_value(self._default)


class ComboBox(QtWidgets.QComboBox, PreferenceBase):
    """A combobox preference widget."""

    @classmethod
    def from_component(cls, component: Component):
        inst = cls(
            component.data_type, component.value, component.default, component.items()
        )
        inst.set_component(component)
        return inst

    def __init__(
        self,
        data_type: type,
        value: str,
        default: str,
        items: list[DataTypes],
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        self._data_type = data_type
        self._default = default
        self.addItems([str(item) for item in items])
        self.setCurrentText(value)
        self.currentIndexChanged.connect(self._on_index_changed)

    @QtCore.Slot(int)
    def _on_index_changed(self, index: int) -> None:
        super().set_value(self.currentText())

    def get_value(self):
        return self._data_type(self.currentText())

    def set_value(self, value: str):
        self.setCurrentText(str(value))

    def restore_default(self):
        self.set_value(self._default)


class ColorPicker(QtWidgets.QWidget, PreferenceBase):
    """A color picker preference widget."""

    @classmethod
    def from_component(cls, component: Component):
        inst = cls(component.value, component.default)
        inst.set_component(component)
        return inst

    def __init__(
        self,
        value: QtGui.QColor,
        default: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._picker = _ColorPicker(parent=self)
        self._picker.set_color(value)
        self._color = value
        self._picker.color_changed.connect(self._on_color_changed)
        layout.addWidget(self._picker)
        self._default = default

    @QtCore.Slot(QtGui.QColor)
    def _on_color_changed(self, color: QtGui.QColor) -> None:
        r, g, b, a = color.getRgb()
        color_str = f"{r},{g},{b},{a}"
        super().set_value(color_str)
        self._color = color_str

    def get_value(self):
        return self._color

    def set_value(self, value: str):
        self._picker.set_csv(value)

    def restore_default(self):
        self.set_value(self._default)


class RadioButtons(QtWidgets.QWidget, PreferenceBase):
    """A radio button preference widget."""

    @classmethod
    def from_component(cls, component: Component):
        inst = cls(component.value, component.default, component.items())
        inst.set_component(component)
        return inst

    def __init__(
        self,
        value: bool,
        default: bool,
        items: list[DataTypes],
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        self._default = default

        layout = QtWidgets.QHBoxLayout(self)
        self._items = items
        self._btn_grp = QtWidgets.QButtonGroup(self)

        for i, item in enumerate(items):
            btn = QtWidgets.QRadioButton(str(item), self)
            btn.setChecked(item == value)
            btn.clicked.connect(self._on_clicked)
            layout.addWidget(btn)
            self._btn_grp.addButton(btn, i)

        layout.addStretch()

    @QtCore.Slot()
    def _on_clicked(self) -> None:
        value = self._items[self._btn_grp.checkedId()]
        super().set_value(value)

    def get_value(self) -> bool:
        return self._items[self._btn_grp.checkedId()]

    def set_value(self, value: DataTypes) -> None:
        self._btn_grp.button(self._items.index(value)).setChecked(True)

    def restore_default(self) -> None:
        self.set_value(self._default)


class Slider(QtWidgets.QWidget, PreferenceBase):
    """A slider preference widget."""

    # value_changed signal is added here (overriding the PreferenceBase)
    # to avoid the signals and slots in QMetaObject Sort Warning and
    # allow connections to be made to the signal without problems.
    value_changed = QtCore.Signal(object)

    FieldPositionLeft = "left"
    FieldPositionRight = "right"
    FieldPositionNone = "none"

    @classmethod
    def from_component(cls, component: Component):
        inst = cls(
            component.data_type,
            component.value,
            component.default,
            component.range,
            component.step,
            component.field,
        )
        inst.set_component(component)
        return inst

    def __init__(
        self,
        data_type: type,
        value: DataTypes,
        default: DataTypes,
        range_: tuple[Number, Number],
        step: Number,
        field: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        self._data_type = data_type
        self._default = default
        self._range = range_
        self._step = step
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if data_type == int:
            self._slider = IntSlider(range_[0], range_[1], step)
        elif data_type == float:
            self._slider = FloatSlider(range_[0], range_[1], step)
        self._slider.set_value(value)
        self._field = Field(data_type, value, default, range_)
        layout.addWidget(self._slider)
        if field == self.FieldPositionLeft:
            layout.insertWidget(0, self._field)
        elif field == self.FieldPositionRight:
            layout.insertWidget(1, self._field)
        elif field == self.FieldPositionNone:
            self._field.hide()
        else:
            raise ValueError(f"Invalid field position: {field}")
        layout.setStretchFactor(self._slider, 1)
        # Connect signals
        self._slider.value_changed.connect(self._on_slider_changed)
        self._field.value_changed.connect(self._on_field_changed)

    @QtCore.Slot(object)
    def _on_slider_changed(self, value: object) -> None:
        with block_signals(self._field):
            self._field.set_value(value)
        super().set_value(value)

    @QtCore.Slot(object)
    def _on_field_changed(self, value: object) -> None:
        if value < self._range[0]:
            value = self._range[0]
        elif value > self._range[1]:
            value = self._range[1]
        with block_signals(self._slider):
            self._slider.setValue(value)

    @QtCore.Slot()
    def get_value(self) -> DataTypes:
        return self._field.get_value()

    def set_value(self, value: DataTypes) -> None:
        self.setValue(value)

    def restore_default(self) -> None:
        self.set_value(self._default)
