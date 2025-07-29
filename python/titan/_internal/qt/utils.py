"""Some generic qt utilities I haven't find a better place for"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from titan.qt import QtCore, QtGui, QtWidgets, QT_VERSION

from titan.preferences import Preferences
from titan._internal.preferences.protocols import WindowPreferences


def _validate_preferences(preferences: WindowPreferences) -> bool:
    """Validate that the preferences contain the expected keys.

    Args:
        preferences: The preferences to validate.

    Raises:
        ValueError: If the preferences are invalid.

    Returns:
        bool: True if the preferences are valid.
    """
    width = preferences.get_component("win/width")
    height = preferences.get_component("win/height")
    x_pos = preferences.get_component("win/pos/x")
    y_pos = preferences.get_component("win/pos/y")
    if not all([width, height, x_pos, y_pos]):
        raise ValueError(
            "Invalid preferences to store/restore window size and position"
        )
    return True


def restore_window_size_and_position(
    widget: QtWidgets.QWidget, preferences: WindowPreferences
) -> None:
    """Restore the window size and position from the preferences. If the position is not set, center the window.

    Args:
        widget: The widget to resize and move.
        preferences: The preferences to get the window size and position from.
    """
    _validate_preferences(preferences)
    widget.resize(preferences.win.width.value, preferences.win.height.value)
    x_pos = preferences.win.pos.x.value
    y_pos = preferences.win.pos.y.value
    # Will only be None the first time the window is shown, after that the
    # position will be stored in the preferences
    if QT_VERSION > 600000:
        desktop_geometry = QtWidgets.QApplication.primaryScreen().geometry() # type: ignore
    else:
        desktop_geometry = QtWidgets.QApplication.desktop().screenGeometry() # type: ignore
    if x_pos is None:
        x_pos = (desktop_geometry.width() - widget.width()) // 2
        y_pos = (desktop_geometry.height() - widget.height()) // 2
    widget.move(x_pos, y_pos)


def store_window_size_and_position(
    widget: QtWidgets.QWidget, preferences: WindowPreferences
) -> None:
    """Save the window size and position to the preferences.

    Args:
        widget: The widget to get the size and position from.
        preferences: The preferences to store the window size and position in.
    """
    _validate_preferences(preferences)
    preferences.win.width.value = widget.width()
    preferences.win.height.value = widget.height()
    preferences.win.pos.x.value = widget.x()
    preferences.win.pos.y.value = widget.y()
