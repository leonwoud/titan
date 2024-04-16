""" This module contains the main logger GUI components. 

>>> # Open a serialized log file and display it in the logger GUI
>>> from titan.resources import find_resource
>>> from titan._internal.logger.gui.main import TitanLogger
>>> gui_logger = TitanLogger("Example")
>>> log_file = find_resource("log_examples.dat")
>>> gui_logger.load_log(log_file)
>>> gui_logger.show()

"""

import logging
from typing import Optional

# Logger imports
from .model import TitanLoggerModel, FilterProxyModel
from .record import TitanLogRecord, LogRecordInfo
from .view import TitanLoggerView
from .header import Headers, Levels
from .io import write_records, read_records

from titan.preferences import Preferences
from titan.qt import QtCore, QtGui, QtWidgets
from titan.resources import find_resource


# Constants
LOGGER_MODELS: dict[str, TitanLoggerModel] = {}


def get_logger_preferences(name) -> Preferences:
    """Get the logger preferences for a given name."""
    preferences_file = find_resource("logger.preferences")
    application = f"titan.preferences.{name}"
    preferences = Preferences.from_file(preferences_file, application=application)
    return preferences


def get_logger_model(
    name: Optional[str] = None, preferences: Optional[Preferences] = None
):
    """Get the logger model for a given name. If the logger model already exists, return it."""

    # If we're not given a name, use the same root logger model
    if name is None:
        name = "root"

    if preferences is None:
        preferences = get_logger_preferences(name)

    if name not in LOGGER_MODELS:
        LOGGER_MODELS[name] = TitanLoggerModel(preferences)

    return LOGGER_MODELS[name]


class TitanLogger(QtWidgets.QWidget):

    def __init__(
        self, name: Optional[str] = None, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent=parent)
        self._table_view = None
        self._tabel_model = None
        self._name = name
        self._preferences = get_logger_preferences(name)
        self._init_ui()
        self._record_infos = []

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        self._table_view = TitanLoggerView()
        self._table_view.doubleClicked.connect(self._on_double_click)
        self._table_model = get_logger_model(self._name, self._preferences)
        self._proxy_model = FilterProxyModel(self)
        self._proxy_model.setSourceModel(self._table_model)
        self._table_view.filter_changed.connect(self._on_filter_changed)
        self._table_view.set_level_filter(self._preferences.level.value)
        self._table_view.setModel(self._proxy_model)
        layout.addWidget(self._table_view)
        self._copy_action = QtWidgets.QAction(self)
        self._copy_action.triggered.connect(self._on_copy)
        self._copy_action.setShortcut(QtGui.QKeySequence.Copy)
        self.addAction(self._copy_action)

        self.setStyleSheet("QTableView {border: 2px solid transparent;}")

    @QtCore.Slot(int, list)
    def _on_filter_changed(self, col: int, values: list[str]) -> None:
        """Update the filter values in the proxy model.

        Args:
            col: The column index the filter is for"
            values: The filter values
        """
        # If the Level filter is changed, we store this in the preferences
        if col == Headers.Level:
            level_name = values[0]
            # Find the level name in the Levels enum, we're going to get
            # something like "CRITICAL", but we want to store "Critical"
            # in the preferences.
            for Level in Levels:
                if Level.level_name == level_name:
                    self._preferences.level.value = Level.name
                    break
        self._proxy_model.set_filter(col, values)

    @QtCore.Slot()
    def _on_copy(self) -> None:
        """Copy the selected rows to the clipboard."""
        self._table_view.copy_selected()

    @QtCore.Slot(QtCore.QModelIndex)
    def _on_double_click(self, index: QtCore.QModelIndex) -> None:
        """Show the log record info when a row is double clicked."""
        record_index = self._proxy_model.mapToSource(index).row()
        record = self._table_model.get_log_record(record_index)
        info = LogRecordInfo(record, parent=self)
        self._record_infos.append(info)
        info.on_closed.connect(self._on_info_closed)
        info.move(QtGui.QCursor.pos())
        info.show()

    @QtCore.Slot(TitanLogRecord)
    def _on_info_closed(self, info: LogRecordInfo) -> None:
        """Remove the info widget from the list when it is closed."""
        self._record_infos.remove(info)
        info.deleteLater()

    def save_log(self, file_path: str) -> None:
        """Saves the log records to a file."""
        write_records(self._table_model._log_records, file_path)

    def load_log(self, file_path: str) -> None:
        """Loads the log records from a file."""
        self._table_model.set_log_records(read_records(file_path))

    def showEvent(self, event: QtCore.QEvent) -> None:
        """Restore the window state when the logger is shown."""
        # TODO: Only do this if this widget isn't embedded in another window
        self.resize(
            self._preferences.win.width.value, self._preferences.win.height.value
        )
        x_pos = self._preferences.win.pos.x.value
        y_pos = self._preferences.win.pos.y.value
        # Will only be None the first time the window is shown, after that the
        # position will be stored in the preferences
        if x_pos is None:
            desktop_geometry = QtWidgets.QApplication.desktop().screenGeometry()
            x_pos = (desktop_geometry.width() - self.width()) // 2
            y_pos = (desktop_geometry.height() - self.height()) // 2
        self.move(x_pos, y_pos)
        event.accept()

    def closeEvent(self, event: QtCore.QEvent) -> None:
        """Close the log records when the TitanLogger is closed."""
        for info in self._record_infos:
            info.close()
        # Store the window state on close
        self._preferences.win.width.value = self.width()
        self._preferences.win.height.value = self.height()
        self._preferences.win.pos.x.value = self.x()
        self._preferences.win.pos.y.value = self.y()
        event.accept()


class TitanLogHandler(logging.Handler):
    """A logging handler that emits signals to the LoggingGUIModel"""

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = model

    def emit(self, record: logging.LogRecord) -> None:
        log_record = TitanLogRecord.from_record(record)
        self._model.add_log_record(log_record)
