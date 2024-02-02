
from typing import Union

from PySide2 import QtQuickWidgets, QtWidgets, QtCore, QtGui


# Local Imports
from titan.qml import get_component


def color_as_hex(color: Union[str, QtGui.QColor]) -> str:
    """Converts a color to a hex string.

    Args:
        color (Union[str, QtGui.QColor]): The color to convert.
    
    Returns:
        str: The color as a hex string.
    """
    if isinstance(color, QtGui.QColor):
        return color.name()
    color = QtGui.QColor(color)
    return color.name()


class CircularProgressBarProperties(QtCore.QObject):

    """"The properties are used to control the appearance and behavior of 
    the CircularProgressBar widget, that can be manipulated at runtime.
    """

    # General Properties
    value_changed = QtCore.Signal(int)
    height_changed = QtCore.Signal(int)
    width_changed = QtCore.Signal(int)
    reverse_changed = QtCore.Signal(bool)

    # Progress Arc Properties
    progress_size_changed = QtCore.Signal(int)
    progress_color_changed = QtCore.Signal(str)

    # Progress Groove Arc Properties
    groove_size_changed = QtCore.Signal(int)
    groove_color_changed = QtCore.Signal(str)

    # Text properties
    show_percent_changed = QtCore.Signal(bool)
    text_font_changed = QtCore.Signal(str)
    text_size_changed = QtCore.Signal(int)
    text_changed = QtCore.Signal(str)
    text_color_changed = QtCore.Signal(str)

    def __init__(self):
        super(CircularProgressBarProperties, self).__init__()

        # General Properties
        self._value: int = 0
        self._width: int = 100
        self._height: int = 100
        self._reverse: bool = False

        # Progress Arc Properties
        self._progress_size: int = 10
        self._progress_color: str = color_as_hex("skyblue")

        # Progress Groove Arc Properties
        self._groove_size: int = 10
        self._groove_color: str = color_as_hex("dimgray")

        # Text properties
        self._text: str = ""
        self._show_percent: bool = True
        self._text_font: str = "Roboto"
        self._text_size: int = 12
        self._text_color: str = color_as_hex("dimgray")

    @QtCore.Property(bool, notify=reverse_changed)
    def reverse(self):
        """bool: Whether the progress bar should be reversed. Default is False."""
        return self._reverse
    
    @reverse.setter
    def reverse(self, state):
        if state != self._reverse:
            self._reverse = state
            self.reverse_changed.emit(state)

    @QtCore.Property(int, notify=width_changed)
    def width(self):
        """int: The width of the progress bar. Default is 100."""
        return self._width

    @width.setter
    def width(self, w):
        if w != self._width:
            self._height = w
            self.height_changed.emit(w)

    @QtCore.Property(int, notify=height_changed)
    def height(self):
        """int: The height of the progress bar. Default is 100."""
        return self._height
    
    @height.setter
    def height(self, h):
        if h != self._height:
            self._height = h
            self.height_changed.emit(h)

    @QtCore.Property(int, notify=value_changed)
    def value(self):
        """int: The value of the progress bar. Default is 0."""
        return self._value

    @value.setter
    def value(self, v):
        if v != self._value:
            self._value = v
            self.value_changed.emit(v)

    @QtCore.Property(int, notify=progress_size_changed)
    def progress_size(self):
        """int: The size of the progress arc. Default is 10."""
        return self._progress_size

    @progress_size.setter
    def progress_size(self, size):
        if size != self._progress_size:
            self._progress_size = size
            self.progress_size_changed.emit(size)

    @QtCore.Property('QString', notify=progress_color_changed)
    def progress_color(self):
        """str: The color of the progress arc. Default is "skyblue"."""
        return self._progress_color

    @progress_color.setter
    def progress_color(self, color):
        color = color_as_hex(color)
        if color != self._progress_color:
            self._progress_color = color
            self.progress_color_changed.emit(color)

    @QtCore.Property(int, notify=groove_size_changed)
    def groove_size(self):
        """int: The size of the progress groove arc. Default is 10."""
        return self._groove_size

    @groove_size.setter
    def groove_size(self, size):
        if size != self._progress_size:
            self._groove_size = size
            self.groove_size_changed.emit(size)

    @QtCore.Property('QString', notify=groove_color_changed)
    def groove_color(self):
        """str: The color of the progress groove arc. Default is "dimgray"."""
        return self._groove_color

    @groove_color.setter
    def groove_color(self, color):
        color = color_as_hex(color)
        if color != self._groove_color:
            self._groove_color = color
            self.groove_color_changed.emit(color)
    
    @QtCore.Property(bool, notify=show_percent_changed)
    def show_percent(self):
        """bool: Whether to show the percentage text. Default is True."""
        return self._show_percent

    @show_percent.setter
    def show_percent(self, show):
        if show != self._show_percent:
            self._show_percent = show
            self.show_percent_changed.emit(show)

    @QtCore.Property('QString', notify=text_font_changed)
    def text_font(self):
        """str: The font of the percentage text. Default is "Roboto"."""
        return self._text_font
    
    @text_font.setter
    def text_font(self, font):
        if font != self._text_font:
            self._text_font = font
            self.text_font_changed.emit(font)

    @QtCore.Property(int, notify=text_size_changed)
    def text_size(self):
        """int: The size of the percentage text. Default is 12."""
        return self._text_size  
    
    @text_size.setter
    def text_size(self, size):
        if size != self._text_size:
            self._text_size = size
            self.text_size_changed.emit(size)

    @QtCore.Property('QString', notify=text_changed)
    def text(self):
        """str: The text to display. Default is an empty string."""
        return self._text
    
    @text.setter
    def text(self, text_str):
        if text_str != self._text:
            self._text = text_str
            self.text_suffix_changed.emit(text_str)
    
    @QtCore.Property('QString', notify=text_color_changed)
    def text_color(self):
        """str: The color of the percentage text. Default is "dimgray"."""
        return self._text_color
    
    @text_color.setter
    def text_color(self, color):
        color = color_as_hex(color)
        if color != self._text_color:
            self._text_color = color
            self.text_color_changed.emit(color)


class CircularProgressBar(QtQuickWidgets.QQuickWidget):
    def __init__(self, parent=None):
        super(CircularProgressBar, self).__init__(parent)

        # TODO: Should we be able to resize this?
        #self.setResizeMode(QtQuickWidgets.QQuickWidget.SizeRootObjectToView)
        self.setSource(QtCore.QUrl.fromLocalFile(get_component("CircularProgressBar")))
        if self.errors():
            for error in self.errors():
                print(error)
            raise
            
        # Make sure the widget is transparent.
        self.setAttribute(QtCore.Qt.WA_AlwaysStackOnTop)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setClearColor(QtCore.Qt.transparent)
        
        # Setup the binding
        self.properties = CircularProgressBarProperties()
        self.engine().rootContext().setContextProperty("properties", self.properties)



EXAMPLE_WINDOW = None


if __name__ == "__main__":

    from maya import OpenMayaUI
    import shiboken2

    """Example usage of the CircularProgressBar widget.
    """

    ptr = OpenMayaUI.MQtUtil.mainWindow()
    handle = int(ptr)
    maya_window = shiboken2.wrapInstance(handle, QtWidgets.QWidget)

    EXAMPLE_WINDOW = QtWidgets.QWidget(parent=maya_window)
    setattr(EXAMPLE_WINDOW, "counter", 0)
    layout = QtWidgets.QHBoxLayout(EXAMPLE_WINDOW)

    progress_bar = CircularProgressBar(parent=EXAMPLE_WINDOW)

    layout.addWidget(progress_bar)

    def on_timeout():
        EXAMPLE_WINDOW.counter = (EXAMPLE_WINDOW.counter + 1) % 100
        progress_bar.properties.value = EXAMPLE_WINDOW.counter

    timer = QtCore.QTimer(EXAMPLE_WINDOW)
    timer.setInterval(25)
    timer.timeout.connect(on_timeout)
    timer.start()

    EXAMPLE_WINDOW.closeEvent = lambda _: timer.stop()
    EXAMPLE_WINDOW.setWindowFlags(QtCore.Qt.Window)
    EXAMPLE_WINDOW.show()
