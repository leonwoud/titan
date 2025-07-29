from __future__ import absolute_import

from titan.utils import DummyClass, dummy_function

QT_AVAILABLE = False
QT_VERSION = None
wrap_instance = None
QtCore = QtGui = QtWidgets = QtQuickWidgets = QtTest = None

qt_bindings = [
    ("PySide2", "shiboken2"),
    ("PySide6", "shiboken6"),
]

for qt_mod, shiboken_mod in qt_bindings:
    try:
        qt = __import__(qt_mod, fromlist=["QtCore", "QtGui", "QtWidgets", "QtQuickWidgets", "QtTest"])
        shiboken = __import__(shiboken_mod, fromlist=["wrapInstance"])

        QtCore = getattr(qt, "QtCore")
        QtGui = getattr(qt, "QtGui")
        QtWidgets = getattr(qt, "QtWidgets")
        QtQuickWidgets = getattr(qt, "QtQuickWidgets")
        QtTest = getattr(qt, "QtTest")
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
    QtTest = DummyClass
    wrap_instance = dummy_function
else:
    version_str = QtCore.qVersion() # type: ignore
    major, minor, patch = map(int, version_str.split('.'))
    version_num_str = f"{major:02d}{minor:02d}{patch:03d}"
    QT_VERSION = int(version_num_str)

def is_qt_app():
    return QT_AVAILABLE and bool(QtWidgets.QApplication.instance()) # type: ignore


__all__ = (
    "QT_AVAILABLE",
    "wrap_instance",
    "QtCore",
    "QtGui",
    "QtWidgets",
    "QtQuickWidgets",
    "QtTest",
    "is_qt_app",
)
