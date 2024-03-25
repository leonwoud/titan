from functools import cache
from typing import Optional

from titan.qt import QtWidgets, QtGui, QtCore

"""
import titan.widgets.collapsible_container
import imp
imp.reload(titan.widgets.collapsible_container)
from titan.widgets.collapsible_container import _CollapsibleTitleBar

w = _CollapsibleTitleBar(height=20, label="test")
w.show()
"""


ARROW_IMG = [
    "11 11 2 1",
    "  c None",
    "x c {}",
    "           ",
    "           ",
    "           ",
    "xxxxxxxxxxx",
    " xxxxxxxxx ",
    "  xxxxxxx  ",
    "   xxxxx   ",
    "    xxx    ",
    "     x     ",
    "           ",
    "           ",
]


@cache
def _get_pixmap(collapsed: bool, color: str) -> QtGui.QPixmap:
    """Returns an arrow pixmap icon.

    Args:
        collapsed (bool): If True, draws the arrow pointing to the right, otherwise down.
        colour (str): The color (hex) of the arrow.

    Returns:
        PySide.QtGui.QPixMap: Icon pixmap.
    """
    arrow = ARROW_IMG
    arrow[2] = arrow[2].format(color)
    pixmap = QtGui.QPixmap(arrow)
    if collapsed:
        xform = QtGui.QTransform()
        xform.rotate(270)
        pixmap = pixmap.transformed(xform)
    return pixmap


class _CollapsibleTitleBar(QtWidgets.QPushButton):
    """Collapsible title bar widget.

    The Title Bar for an optionally collapsible container. If
    collapsible, an icon will be drawn on the left side of the
    title bar to indicate the current collapsed state of the container.

    Intended to be used with the CollpsibleContainer widget.

    Args:
        text (str): Title text.
        height (int): Fixed height of header.
    """

    def __init__(
        self,
        label: str,
        height: int,
        is_collapsible: Optional[bool] = True,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super(_CollapsibleTitleBar, self).__init__(label, parent=parent)
        self._is_collapsible = is_collapsible
        self._collapsed = False
        self.setFixedHeight(height)
        self.clicked.connect(self._on_clicked)

    def is_collapsed(self) -> bool:
        """Returns True if currently in a collapsed state."""
        return self._collapsed

    def set_collapsed_state(self, state: bool) -> None:
        """Set the buttons collapsed state.
        Args:
            state (bool): The new collapsed state.
        """
        self._collapsed = state

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Reimplement to draw the title bar."""
        painter = QtGui.QPainter(self)
        painter.initFrom(self)
        painter.setRenderHint(painter.Antialiasing, True)
        color = self.palette().color(QtGui.QPalette.Light)
        text_color = self.palette().color(QtGui.QPalette.ButtonText)
        # Draw the background color
        painter.fillRect(0, 0, event.rect().width(), self.minimumHeight(), color)
        # Draw the arrow icon
        if self._is_collapsible:
            painter.drawPixmap(8, 4, _get_pixmap(self._collapsed, text_color.name()))
        # Lastly draw the text
        if self.text():
            painter.drawText(
                30,
                0,
                event.rect().width(),
                self.minimumHeight(),
                QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                self.text(),
            )

    @QtCore.Slot()
    def _on_clicked(self):
        """Toggle the collapsed state when clicked"""
        self._collapsed = not self._collapsed
        self.update()


class CollapsibleContainer(QtWidgets.QWidget):
    """Collapsible Container like widget that provides a vertical layout.

    Note: If you want the widget to be collapsed by default, call "collapse"
          _after_ adding the contents to the CollapsibleGroupBox so we have an
          accurate size hint.

    Args:
        title (str): Title text
        height (int): The height title bar (and size when collapsed)
        parent (QWidget): The parent widget (if any)
    """

    collapsed_state_changed = QtCore.Signal(bool)

    def __init__(self, title: Optional[str] = None, height=20, parent=None):
        super().__init__(parent=parent)
        self._height = height
        self._titlebar = _CollapsibleTitleBar(title, height)
        self._contents = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._titlebar)
        main_layout.addWidget(self._contents)
        self._expanded_size_hint = None
        self._titlebar.clicked.connect(self._on_clicked)

    def is_collapsed(self):
        """Returns True if the widget has been expanded, False otherwise"""
        return self._contents.isHidden()

    def collapse(self, state: bool) -> None:
        """Sets the collapsed state for this CollapsibleContainer.

        Args:
            state (bool): True to collapse the widget, False to expand it.
        """
        currently_collapsed = self.is_collapsed()
        if state == currently_collapsed:
            return

        if not currently_collapsed:
            self._size_hint = self.sizeHint()

        self._contents.setHidden(state)

        if state:
            self.setMinimumHeight(self._height)
            self.setMaximumHeight(self._height)
        else:
            self.setMinimumHeight(self._size_hint.height())
            self.setMaximumHeight(self._size_hint.height())

        self._titlebar.set_collapsed_state(state)
        self.collapsed_state_changed.emit(state)

    @QtCore.Slot()
    def _on_clicked(self):
        """Callback for toggling the collapse state."""
        self.collapse(not self.is_collapsed())

    @property
    def contents_widget(self) -> QtWidgets.QWidget:
        return self._contents
