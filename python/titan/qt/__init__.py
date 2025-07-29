from __future__ import absolute_import
from typing import TYPE_CHECKING

from titan.utils import DummyClass, dummy_function

QT_AVAILABLE: bool = False
QT_VERSION: int = -1
wrap_instance = None

try:
    from PySide6 import QtCore, QtGui, QtQuickWidgets, QtTest, QtWidgets # type: ignore
    from shiboken6 import wrapInstance as wrap_instance # type: ignore
    QT_AVAILABLE = True
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtQuickWidgets, QtTest, QtWidgets # type: ignore
        from shiboken2 import wrapInstance as wrap_instance # type: ignore
        QT_AVAILABLE = True
    except ImportError:
        pass


if QT_AVAILABLE:
    version_str = QtCore.qVersion() # type: ignore
    major, minor, patch = map(int, version_str.split('.'))
    version_num_str = f"{major:02d}{minor:02d}{patch:03d}"
    QT_VERSION = int(version_num_str)

else:
    # At Runtime, if Qt isn't available in the env we replace these
    # with the DummyClass that allows modules to import, so even testing
    # that Qt is available is possible. Not much can be done without Qt
    # in the env though...
    if not TYPE_CHECKING:
        QtCore = DummyClass
        QtGui = DummyClass
        QtQuickWidgets = DummyClass
        QtTest = DummyClass
        QtWidgets = DummyClass


def is_qt_app():
    return QT_AVAILABLE and bool(QtWidgets.QApplication.instance()) # type: ignore


__all__ = (
    "QT_AVAILABLE",
    "QT_VERSION",
    "wrap_instance",
    "QtCore",
    "QtGui",
    "QtWidgets",
    "QtQuickWidgets",
    "QtTest",
    "is_qt_app",
)
