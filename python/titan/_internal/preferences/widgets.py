from typing import Optional

from titan.qt import QtCore, QtGui, QtWidgets

from .components import Component, DataTypes, Number


class PreferenceBase(QtCore.QObject):
    """Base class for preference widgets.

    This class provides a common interface for preference widgets to be used in the preferences
    dialog. It provides a way to get and set values from the preferences and a way to reset the
    values to their defaults.
    """

    def __init__(self):
        super().__init__()
        self._component = None

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
        print(f"Setting value for {self._component.path} to {value}")
        self._component.preferences.set_value(self._component.path, value)

    def restore_default(self):
        """Reset the widget to its default value."""
        raise NotImplementedError

    def reload(self):
        """Reload the value from the preferences."""
        value = self._component.get_value()
        self.set_value(value)


class CheckBox(QtWidgets.QCheckBox, PreferenceBase):
    """A checkbox preference widget."""

    @classmethod
    def from_component(cls, component: Component):
        value = component.preferences.get_value(component.path)
        if value is None:
            value = component.default
        inst = cls(value, component.default)
        inst.set_component(component)
        return inst

    def __init__(
        self,
        value: bool,
        default: bool,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        self._default = default
        self.setChecked(value)
        self.stateChanged.connect(self._on_state_changed)

    @QtCore.Slot(bool)
    def _on_state_changed(self, value: bool) -> None:
        # Only update the preferences if the value has changed
        super().set_value(value)

    def get_value(self) -> bool:
        return self.isChecked()

    def set_value(self, value: bool) -> None:
        self.setChecked(value)

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
            component.get_value(),
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
        if value is None:
            value = default
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
        value = component.get_value()
        inst = cls(component.data_type, value, component.default, component.items())
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
