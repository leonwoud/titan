from typing import Optional

from titan.qt import QtCore, QtGui, QtWidgets
from .header import Headers, Filters, Levels, TitanLoggerFilterHeaderView


class NoFocusDelegate(QtWidgets.QStyledItemDelegate):
    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        itemOption = QtWidgets.QStyleOptionViewItem(option)
        if option.state & QtWidgets.QStyle.State_HasFocus:
            itemOption.state = itemOption.state ^ QtWidgets.QStyle.State_HasFocus
        super().paint(painter, itemOption, index)


class TitanLoggerView(QtWidgets.QTableView):

    filter_changed = QtCore.Signal(int, list)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        horiztonal_header = TitanLoggerFilterHeaderView(QtCore.Qt.Horizontal, self)
        horiztonal_header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.create_filters(horiztonal_header)
        self.setHorizontalHeader(horiztonal_header)
        horiztonal_header.setStretchLastSection(True)
        vertical_header = self.verticalHeader()
        vertical_header.hide()
        vertical_header.setDefaultSectionSize(20)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setItemDelegate(NoFocusDelegate())
        self.setShowGrid(False)
        horiztonal_header.filter_changed.connect(self.filter_changed.emit)

    def create_filters(self, header: TitanLoggerFilterHeaderView) -> None:
        """Create filters for the HeaderView."""
        for col in Headers:
            filter = Filters[col](self)
            header.add_filter(filter)
        level_filter = header.get_filter(Headers.Level)
        for level in Levels:
            level_filter.addItem(level.name, level.level_name)
        level_filter.insertSeparator(1)

    def copy_selected(self) -> None:
        """Copy the selected rows to the clipboard."""
        selection_model = self.selectionModel()
        indexes = selection_model.selectedIndexes()
        if not indexes:
            return
        source_model = self.model().sourceModel()
        selection_model = self.selectionModel()
        selected_rows = [
            self.model().mapToSource(index).row()
            for index in selection_model.selectedRows()
        ]
        records = [source_model.get_log_record(row) for row in selected_rows]
        text = "\n".join([str(record) for record in records])
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(text)
