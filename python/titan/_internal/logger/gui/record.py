from __future__ import annotations

from datetime import datetime
import logging
from typing import Mapping, Optional

from titan.qt import QtCore, QtGui, QtWidgets


class TitanLogRecord:

    @classmethod
    def from_record(cls, record: logging.LogRecord) -> TitanLogRecord:
        """Create a TitanLogRecord from a logging.LogRecord."""
        inst = cls()
        inst.created = record.created
        inst.time_str = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        inst.file_name = record.filename
        inst.module = record.module
        inst.name = record.name
        inst.msg = record.getMessage()
        inst.level_name = record.levelname
        inst.level_number = record.levelno
        inst.path_name = record.pathname
        inst.line_num = record.lineno
        inst.func = record.funcName
        inst.exc_text = record.exc_text
        return inst

    def __str__(self):
        """Return a string representation of the log record."""
        return f"{self.time_str} : {self.level_name} : {self.name} : {self.msg}"

    def __init__(self):
        self.created: float = None
        self.time_str: str = None
        self.file_name: str = None
        self.module: str = None
        self.name: str = None
        self.msg: str = None
        self.level_name: str = None
        self.level_number: int = None
        self.path_name: str = None
        self.line_num: int = None
        self.func: Optional[str] = None
        self.exc_text: Optional[str] = None

    def as_dict(self) -> Mapping[str, str]:
        """Return the log record as a dictionary."""
        return {
            "created": self.created,
            "time_str": self.time_str,
            "file_name": self.file_name,
            "module": self.module,
            "name": self.name,
            "msg": self.msg,
            "level_name": self.level_name,
            "level_number": self.level_number,
            "path_name": self.path_name,
            "line_num": self.line_num,
            "func": self.func,
            "exc_text": self.exc_text,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, str]) -> TitanLogRecord:
        """Create a TitanLogRecord from a dictionary."""
        inst = cls()
        inst.created = data["created"]
        inst.time_str = data["time_str"]
        inst.file_name = data["file_name"]
        inst.module = data["module"]
        inst.name = data["name"]
        inst.msg = data["msg"]
        inst.level_name = data["level_name"]
        inst.level_number = data["level_number"]
        inst.path_name = data["path_name"]
        inst.line_num = data["line_num"]
        inst.func = data["func"]
        inst.exc_text = data["exc_text"]
        return inst


class DocumentFitTextEdit(QtWidgets.QTextEdit):
    """A QTextEdit that resizes to fit the document size."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super(DocumentFitTextEdit, self).__init__(parent=parent)
        self.document().documentLayout().documentSizeChanged.connect(
            self._on_document_changed
        )
        self.setReadOnly(True)

    def _on_document_changed(self, size):
        self.setMaximumHeight(size.height() + 5)


class ElidingLineEdit(QtWidgets.QLineEdit):
    """A QLineEdit that elides the text when it is too long."""

    def __init__(self, text, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super(ElidingLineEdit, self).__init__(text, parent=parent)
        self._text = text
        self.setReadOnly(True)

    def resizeEvent(self, event):
        fm = QtGui.QFontMetrics(self.font())
        self.setText(
            fm.elidedText(self._text, QtCore.Qt.ElideRight, event.size().width())
        )
        event.accept()


class LogRecordInfo(QtWidgets.QWidget):

    on_closed = QtCore.Signal(object)

    def __init__(
        self, record: TitanLogRecord, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super(LogRecordInfo, self).__init__(parent=parent)
        self.setWindowTitle("Titan Log Record")
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        layout = QtWidgets.QFormLayout()
        layout.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        main_layout.addLayout(layout)
        # Date
        date_txt = datetime.fromtimestamp(record.created).strftime(
            "%I:%M:%S%p %A, %d %B %Y"
        )
        time = ElidingLineEdit(date_txt, self)
        layout.addRow("Time:", time)
        # Path
        path = ElidingLineEdit(record.path_name, self)
        layout.addRow("Path:", path)
        # Module
        module = ElidingLineEdit(record.module, self)
        layout.addRow("Module:", module)
        # Function
        function = ElidingLineEdit(record.func, self)
        layout.addRow("Function:", function)
        # Line
        line = ElidingLineEdit(str(record.line_num), self)
        layout.addRow("Line:", line)
        # Level
        level = ElidingLineEdit(record.level_name, self)
        layout.addRow("Level:", level)
        # Message
        msg = DocumentFitTextEdit(self)
        msg.setPlainText(record.msg)
        layout.addRow("Message:", msg)
        # Traceback
        if record.exc_text:
            exc_text = DocumentFitTextEdit(self)
            exc_text.setPlainText(record.exc_text)
            layout.addRow("Traceback:", exc_text)
        # TODO: Can we do without stylesheet?
        self.setStyleSheet(
            "QLineEdit,QTextEdit { border: 0px; background: transparent; font-family: Courier New}"
        )
        main_layout.addStretch()

    def closeEvent(self, event: QtCore.QEvent) -> None:
        """Emit the on_closed signal when the widget is closed."""
        self.on_closed.emit(self)
        event.accept()
        super(LogRecordInfo, self).closeEvent(event)
