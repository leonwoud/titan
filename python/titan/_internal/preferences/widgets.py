from titan.qt import QtWidgets, QtCore


class PreferenceBase(QtCore.QObject):

    preference_changed = QtCore.Signal()

    """Base class for preference widgets.

    This class provides a common interface for preference widgets to be used in the preferences
    dialog. It provides a way to get and set values from the preferences and a way to reset the
    values to their defaults.
    """

    def __init__(self):
        super().__init__()

    def get_value(self):
        """Get the value from the widget."""
        raise NotImplementedError

    def set_value(self, value):
        """Set the value in the widget."""
        raise NotImplementedError

    def reset(self):
        """Reset the widget to its default value."""
        raise NotImplementedError


class CheckBox(QtWidgets.QCheckBox, PreferenceBase):
    """A checkbox preference widget."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def get_value(self):
        return self.isChecked()

    def set_value(self, value):
        self.setChecked(value)

    def reset(self):
        self.setChecked(False)
