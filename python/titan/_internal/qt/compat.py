from titan.qt import QT_VERSION, QtWidgets, QtGui

# Qt6
if QT_VERSION > 500000:
    QAction = QtGui.QAction # type: ignore

# Qt5
else:
    QAction = QtWidgets.QAction # type: ignore


__all__ = ("QAction",)