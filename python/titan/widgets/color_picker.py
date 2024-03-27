from titan.qt import QtCore, QtGui, QtWidgets


class ColorPicker(QtWidgets.QPushButton):

    color_changed = QtCore.Signal(QtGui.QColor)

    def __init__(self, alpha=False, parent=None):
        super(ColorPicker, self).__init__(parent=parent)
        self._include_alpha = alpha
        self.setAutoFillBackground(True)
        self.setFixedSize(20, 20)
        self._setup_widget()

    def _setup_widget(self):
        self.clicked.connect(self._on_click)
        if self._include_alpha:
            self.set_rgba(128, 128, 128, 255)
        else:
            self.set_rgb(128, 128, 128)

    @QtCore.Slot()
    def _on_click(self):
        kwargs = {}
        if self._include_alpha:
            kwargs["options"] = QtWidgets.QColorDialog.ShowAlphaChannel
        color = QtWidgets.QColorDialog.getColor(self._color, **kwargs)
        if color.isValid():
            self._set_color(color)

    def _set_color(self, color: QtGui.QColor) -> None:
        """Store the color and emit the color_changed signal."""
        if self._include_alpha:
            self.set_rgba(color.red(), color.green(), color.blue(), color.alpha())
        else:
            self.set_rgb(color.red(), color.green(), color.blue())

    def set_hex(self, hex_code: str) -> None:
        """Set the color using a hex code."""
        self.setStyleSheet(f"background-color: {hex_code};")
        self._color = QtGui.QColor(hex_code)
        self.color_changed.emit(self._color)

    def set_rgb(self, red: int, green: int, blue: int) -> None:
        """Set the color using RGB values."""
        self.setStyleSheet(f"background-color: rgb({red}, {green}, {blue});")
        self._color = QtGui.QColor(red, green, blue)
        self.color_changed.emit(self._color)

    def set_rgba(self, red: int, green: int, blue: int, alpha: int) -> None:
        """Set the color using RGBA values."""
        self.setStyleSheet(f"background-color: rgba({red}, {green}, {blue}, {alpha});")
        self._color = QtGui.QColor(red, green, blue, alpha)
        self.color_changed.emit(self._color)

    def set_csv(self, data: str):
        """Set the color using a CSV string.

        This is expected to be rgb or rgba values."""
        color = QtGui.QColor(*[int(c.strip()) for c in data.split(",")])
        self._set_colour(color)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Overriden function."""
        super(ColorPicker, self).paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(painter.Antialiasing)
        height = self.rect().height()
        width = self.rect().width()
        top = QtCore.QPoint(width, height - 5)
        bottom_right = QtCore.QPoint(width, height)
        bottom_left = QtCore.QPoint(width - 5, +height)
        triangle = QtGui.QPolygon((top, bottom_right, bottom_left))
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 255), QtCore.Qt.SolidPattern)
        painter.setBrush(brush)
        painter.drawPolygon(triangle)
        painter.end()
