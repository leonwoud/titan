from __future__ import absolute_import

from titan.utils import DummyClass, dummy_function

QT_AVAILABLE = False
wrap_instance = None
QtCore = QtGui = QtWidgets = QtQuickWidgets = None

qt_bindings = [
    ("PySide2", "shiboken2"),
    ("PySide6", "shiboken6"),
]

for qt_mod, shiboken_mod in qt_bindings:
    try:
        qt = __import__(qt_mod, fromlist=["QtCore", "QtGui", "QtWidgets", "QtQuickWidgets"])
        shiboken = __import__(shiboken_mod, fromlist=["wrapInstance"])

        QtCore = getattr(qt, "QtCore")
        QtGui = getattr(qt, "QtGui")
        QtWidgets = getattr(qt, "QtWidgets")
        QtQuickWidgets = getattr(qt, "QtQuickWidgets")
        wrap_instance = getattr(shiboken, "wrapInstance")

        QT_AVAILABLE = True
        break
    except ImportError:
        continue


if not QT_AVAILABLE:
    QtCore = DummyClass
    QtGui = DummyClass
    QtWidgets = DummyClass
    QtQuickWidgets = DummyClass
    wrap_instance = dummy_function


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
