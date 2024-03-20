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
from typing import Mapping, Optional

from .model import TitanLoggerModel, FilterProxyModel
from .record import TitanLogRecord, LogRecordInfo
from .view import TitanLoggerView
from .io import write_records, read_records


# Local Imports
from titan.qt import QtCore, QtGui, QtWidgets


# Constants
LOGGER_MODELS: Mapping[str, TitanLoggerModel] = {}
SHARED_LOGGER_MODEL: TitanLoggerModel = None


def get_logger_model(name: Optional[str] = None):
    """Get the logger model for a given name. If the logger model already exists, return it."""

    if name is None:
        global SHARED_LOGGER_MODEL
        if not SHARED_LOGGER_MODEL:
            SHARED_LOGGER_MODEL = TitanLoggerModel()
        return SHARED_LOGGER_MODEL

    if name not in LOGGER_MODELS:
        LOGGER_MODELS[name] = TitanLoggerModel()
    return LOGGER_MODELS[name]


class TitanLogger(QtWidgets.QWidget):

    def __init__(
        self, name: Optional[str] = None, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super(TitanLogger, self).__init__(parent=parent)
        self._table_view = None
        self._tabel_model = None
        self._name = name
        self._init_ui()
        self._record_infos = []

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        self._table_view = TitanLoggerView()
        self._table_view.doubleClicked.connect(self._on_double_click)
        self._table_model = get_logger_model(self._name)
        self._proxy_model = FilterProxyModel(self)
        self._proxy_model.setSourceModel(self._table_model)
        self._table_view.filter_changed.connect(self._proxy_model.set_filter)
        self._table_view.setModel(self._proxy_model)
        layout.addWidget(self._table_view)

        self._copy_action = QtWidgets.QAction(self)
        self._copy_action.triggered.connect(self._on_copy)
        self._copy_action.setShortcut(QtGui.QKeySequence.Copy)
        self.addAction(self._copy_action)

        self.setStyleSheet("QTableView {border: 2px solid transparent;}")

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


class TitanLogHandler(logging.Handler):
    """A logging handler that emits signals to the LoggingGUIModel"""

    def __init__(self, model, *args, **kwargs):
        super(TitanLogHandler, self).__init__(*args, **kwargs)
        self._model = model

    def emit(self, record: logging.LogRecord) -> None:
        log_record = TitanLogRecord.from_record(record)
        self._model.add_log_record(log_record)
