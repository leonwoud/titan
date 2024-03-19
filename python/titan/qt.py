from __future__ import absolute_import

from titan.utils import DummyClass, dummy_function

try:
    from shiboken2 import wrapInstance as wrap_instance
    from PySide2 import QtCore, QtGui, QtWidgets, QtQuickWidgets

    QT_AVAILABLE = True

except ImportError:
    QtCore = DummyClass
    QtGui = DummyClass
    QtWidgets = DummyClass
    QtQuickWidgets = DummyClass
    wrap_instance = dummy_function

    QT_AVAILABLE = False


def is_qt_app():
    return QT_AVAILABLE and bool(QtWidgets.QApplication.instance())


__all__ = (
    "QT_AVAILABLE",
    "wrap_instance",
    "QtCore",
    "QtGui",
    "QtWidgets",
    "QtQuickWidgets",
    "is_qt_app",
)
