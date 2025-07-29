"""This module contains the main logger GUI components.

>>> # Open a serialized log file and display it in the logger GUI
>>> from titan.resources import find_resource
>>> from titan._internal.logger.gui.main import LoggerWidget
>>> gui_logger = LoggerWidget("Example")
>>> log_file = find_resource("log_examples.dat")
>>> gui_logger.load_log(log_file)
>>> gui_logger.show()

"""

from __future__ import annotations

import logging
from typing import Optional, cast

# Logger imports
from .model import TitanLoggerModel, FilterProxyModel
from .record import TitanLogRecord, LogRecordInfo
from .view import TitanLoggerView
from .header import Headers, Levels
from .io import write_records, read_records

from titan._internal.preferences.main import PreferencesDialog
from titan.preferences import Preferences
from titan.qt import QtCore, QtGui, QtWidgets
from titan.qt.compat import QAction
from titan.resources import find_resource

from titan._internal.qt.utils import (
    restore_window_size_and_position,
    store_window_size_and_position,
)
from titan._internal.preferences.protocols import LoggerPreferences, WindowPreferences


# Constants
LOGGER_MODELS: dict[str, TitanLoggerModel] = {}


def get_logger_preferences(name: Optional[str] = None) -> LoggerPreferences:
    """Get the shared logger preferences (same for all loggers)."""
    preferences_file = find_resource("logger.json")
    application = "titan.preferences.logger"  # Shared application name for all loggers
    preferences = Preferences.from_file(preferences_file, application=application)
    return cast(LoggerPreferences, preferences)


def get_logger_model(
    name: Optional[str] = None, preferences: Optional[LoggerPreferences] = None
) -> TitanLoggerModel:
    """Get the logger model for a given name. Each logger has its own model but shared preferences."""

    # If we're not given a name, use the default logger model
    if name is None:
        name = "root"

    if preferences is None:
        preferences = get_logger_preferences()

    if name not in LOGGER_MODELS:
        LOGGER_MODELS[name] = TitanLoggerModel(cast(Preferences, preferences))

    return LOGGER_MODELS[name]


class LoggerWindow(QtWidgets.QMainWindow):
    def __init__(
        self, name: Optional[str] = None, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Titan Logger")
        self._preferences = get_logger_preferences()
        self._logger = LoggerWidget(name, self._preferences, self)
        self.setCentralWidget(self._logger)
        self._init_menu()
        self._prefs_widget = None

    def _init_menu(self) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        edit_menu = menu_bar.addMenu("&Edit")
        
        # File menu actions
        open_action = QAction("&Open...", self)
        open_action.triggered.connect(self._on_open)
        save_action = QAction("&Save", self)
        save_action.triggered.connect(self._on_save)
        
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        
        # Edit menu actions
        edit_prefs = QAction("&Preferences", self)
        edit_prefs.triggered.connect(self._on_edit_prefs)
        edit_menu.addAction(edit_prefs)

    @QtCore.Slot()
    def _on_open(self) -> None:
        """Open a log file in a new logger window."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Log File", "", "Log Files (*.dat)"
        )
        if file_path:
            # Extract filename for window title and unique logger name
            import os
            filename = os.path.basename(file_path)
            logger_name = f"file_{filename}"
            
            # Create a new logger window for this file
            # Set parent to self to keep it alive, but with Qt.Window flag to make it independent
            file_logger_window = LoggerWindow(name=logger_name, parent=self)
            file_logger_window.setWindowFlags(QtCore.Qt.WindowType.Window)
            file_logger_window.setWindowTitle(f"Titan Logger - {filename}")
            file_logger_window.open_log(file_path)
            file_logger_window.show()

    @QtCore.Slot()
    def _on_save(self) -> None:
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Log", "", "Log Files (*.dat)"
        )
        if file_path:
            self._logger.save_log(file_path)

    @QtCore.Slot()
    def _on_refresh_requested(self):
        """Refresh the logger UI when preferences change (e.g., level colors)."""
        # Force sync of preferences to ensure we have the latest values
        cast(Preferences, self._preferences).sync()
        
        # Force a complete refresh of all data in the table model
        model = self._logger._table_model
        view = self._logger._table_view
        
        if model.rowCount() > 0:
            top_left = model.index(0, 0)
            bottom_right = model.index(model.rowCount() - 1, model.columnCount() - 1)
            # Emit dataChanged to force re-evaluation of all roles including colors
            model.dataChanged.emit(top_left, bottom_right)
        
        # Force the view to update its display
        view.viewport().update()
        
        # Also update the current level filter to reflect any preference changes  
        current_level = cast(str, self._preferences.level.value)
        view.set_level_filter(current_level)

    @QtCore.Slot()
    def _on_edit_prefs(self) -> None:
        if self._prefs_widget:
            self._prefs_widget.show()
            self._prefs_widget.raise_()
            return
        self._prefs_widget = PreferencesDialog(
            cast(Preferences, self._preferences), window_title="Titan Logger Preferences", parent=self
        )
        self._prefs_widget.refresh_requested.connect(self._on_refresh_requested)
        self._prefs_widget.show()

    def open_log(self, file_path: str) -> None:
        """Open a log file and display it in the logger GUI."""
        self._logger.load_log(file_path)

    def showEvent(self, event: QtCore.QEvent) -> None:
        """Restore the window state when the logger is shown."""
        # TODO: Only do this is the window is floating, right now it will be
        restore_window_size_and_position(self, cast(WindowPreferences, self._preferences))
        event.accept()

    def closeEvent(self, event: QtCore.QEvent) -> None:
        """Close the log records when the logger window is closed."""
        # Store the window state on close
        store_window_size_and_position(self, cast(WindowPreferences, self._preferences))
        self._logger.close_record_infos()
        event.accept()


class LoggerWidget(QtWidgets.QWidget):

    def __init__(
        self,
        name: Optional[str] = None,
        preferences: Optional[LoggerPreferences] = None,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent=parent)
        self._name = name
        if preferences is None:
            self._preferences = get_logger_preferences()
        else:
            self._preferences = preferences
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
        self._table_view.set_level_filter(cast(str, self._preferences.level.value))
        self._table_view.setModel(self._proxy_model)
        layout.addWidget(self._table_view)
        self._copy_action = QAction(self)
        self._copy_action.triggered.connect(self._on_copy)
        self._copy_action.setShortcut(QtGui.QKeySequence.StandardKey.Copy)
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
                # level_name is added by __new__
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

    def clear_log(self) -> None:
        """Clear the log records."""
        # self._table_model.clear_log()  # TODO: Implement this
        pass

    def close_record_infos(self) -> None:
        """Close all the record info widgets."""
        for info in self._record_infos:
            info.close()


class TitanLogHandler(logging.Handler):
    """A logging handler that emits signals to the LoggingGUIModel"""

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = model

    def emit(self, record: logging.LogRecord) -> None:
        log_record = TitanLogRecord.from_record(record)
        self._model.add_log_record(log_record)
