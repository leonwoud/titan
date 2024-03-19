from __future__ import absolute_import

from titan._internal.host.maya.core import _MayaCore

from titan.logger import get_logger

LOGGER = get_logger("titan.host.maya")


class Maya(metaclass=_MayaCore):
    """This class is used to provide access to the Maya API and UI without
    importing them until they are actually needed and provides protection
    when not in Maya.

    Example:
        >>> # Test if Maya is available
        >>> Maya.is_available
        >>> # Result: True #
        >>> # Test if Maya UI is available
        >>> Maya.ui.is_available
        >>> # Result: True #
        >>> # Alternatively, you can test if Maya is standlone (batch)
        >>> Maya.is_standalone
        >>> # Result: False #
        >>> # Get the Maya main window
        >>> Maya.ui.main_window
        >>> # Result: <PySide2.QtWidgets.QMainWindow(0x600006288f80, name="MayaWindow") at 0x2f9eba440>
    """


IS_MAYA_AVAILABLE = Maya.is_available

if IS_MAYA_AVAILABLE:
    cmds = Maya.cmds
    mel = Maya.mel
    OpenMayaUI = Maya.api.openmayaui
    OpenMaya = Maya.api.openmaya
    OpenMayaAnim = Maya.api.openmayaanim
    OpenMayaRender = Maya.api.openmayarender
    OpenMaya_v1 = Maya.api.openmaya_v1
    MayaEvent = Maya.events
    EventManager = Maya.event_manager

else:
    cmds = None
    mel = None
    OpenMaya = None
    OpenMayaAnim = None
    OpenMayaRender = None
    OpenMaya_v1 = None
    OpenMayaUI = None
    MayaEvent = None
    EventManager = None
