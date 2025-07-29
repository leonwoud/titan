from typing import TYPE_CHECKING, Any, Optional, cast

from titan.preferences import Preferences
from titan.qt import QtCore, QtGui, QtWidgets

from .header import Headers, Levels
from .record import TitanLogRecord

from titan._internal.preferences.protocols import LoggerPreferences


class FilterProxyModel(QtCore.QSortFilterProxyModel):
    """Filter Proxy Model for the logger view."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent=parent)
        self._filters: dict[int, tuple[str, ...]] = {}

    def set_filter(self, col: int, values: list[str]) -> None:
        """Sets the filter values for the given column."""
        if values:
            self._filters[col] = tuple(values)
        else:
            self._filters.pop(col, None)
        # If the level filter is set to any, remove the filter
        if col == Headers.Level and Levels.Any.level_name in values:
            self._filters.pop(col, None)

        self.invalidateFilter()

    def filterAcceptsRow(
        self, row: int, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex
    ) -> bool:
        """Determines if the row should be accepted based on the filters."""
        if not self._filters:
            return True
        source_model = self.sourceModel()

        # Sort out the level filter first
        if Headers.Level in self._filters:
            index = source_model.index(row, Headers.Level, parent)
            level = source_model.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
            if level not in self._filters[Headers.Level]:
                return False

        # The rest of the filters are text filters
        for col in [col for col in Headers if col != Headers.Level]:
            if col in self._filters:
                index = source_model.index(row, col, parent)
                value = source_model.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
                matched = [f for f in self._filters[col] if f.lower() in value.lower()]
                if not matched:
                    return False
        return True


class TitanLoggerModel(QtCore.QAbstractTableModel):

    def __init__(
        self, preferences: Preferences, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent=parent)
        self._log_records = []
        self._prefs = preferences

    def rowCount(
        self,
        parent: (
            QtCore.QModelIndex | QtCore.QPersistentModelIndex
        ) = QtCore.QModelIndex(),
    ) -> int:
        """Return the number of rows in the model."""
        return len(self._log_records)

    def columnCount(
        self,
        parent: (
            QtCore.QModelIndex | QtCore.QPersistentModelIndex
        ) = QtCore.QModelIndex(),
    ) -> int:
        """Return the number of columns in the model."""
        return len(Headers)

    def data(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Return the data for the given index and role."""
        log_record = self._log_records[index.row()]
        level = log_record.level_name

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if index.column() == Headers.Time:
                return log_record.time_str
            elif index.column() == Headers.Level:
                return log_record.level_name
            elif index.column() == Headers.Name:
                return log_record.name
            elif index.column() == Headers.Message:
                return log_record.msg

        elif role == QtCore.Qt.ItemDataRole.FontRole:
            font = QtGui.QFont("Courier New")
            if level == Levels.Critical.level_name:
                font.setBold(True)
            return font

        elif role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == Headers.Level:
                return QtCore.Qt.AlignmentFlag.AlignCenter

        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            if level == Levels.Critical.level_name:
                return cast(LoggerPreferences, self._prefs).colors.critical.value
            elif level == Levels.Error.level_name:
                return cast(LoggerPreferences, self._prefs).colors.error.value
            elif level == Levels.Warning.level_name:
                return cast(LoggerPreferences, self._prefs).colors.warning.value
            elif level == Levels.Info.level_name:
                return cast(LoggerPreferences, self._prefs).colors.info.value
            elif level == Levels.Debug.level_name:
                return cast(LoggerPreferences, self._prefs).colors.info.value
            elif level == Levels.Trace.level_name:
                return cast(LoggerPreferences, self._prefs).colors.trace.value

    def headerData(
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Return the header data for the given section, orientation, and role."""
        if (
            role == QtCore.Qt.ItemDataRole.DisplayRole
            and orientation == QtCore.Qt.Orientation.Horizontal
        ):
            return Headers(section).label

    def add_log_record(self, record: TitanLogRecord) -> None:
        """Add a log record to the model."""
        self._log_records.append(record)
        self.layoutChanged.emit()

    def set_log_records(self, records: list[TitanLogRecord]) -> None:
        """Set the log records for the model."""
        self._log_records = records
        self.layoutChanged.emit()

    def get_log_records(self) -> list[TitanLogRecord]:
        """Return the log records."""
        return [record for record in self._log_records]

    def get_log_record(self, index: int) -> TitanLogRecord:
        """Return the log record at the given index."""
        return self._log_records[index]
