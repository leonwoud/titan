"""
This module provides a set of classes and functions to interact with Maya.
"""

from titan._internal.host.maya import (
    Maya,
    cmds,
    mel,
    OpenMaya,
    OpenMayaAnim,
    OpenMayaRender,
    OpenMaya_v1,
    OpenMayaUI,
    MayaEvent,
    EventManager,
    IS_MAYA_AVAILABLE,
)

__all__ = (
    "IS_MAYA_AVAILABLE",
    "Maya",
    "cmds",
    "mel",
    "OpenMaya",
    "OpenMayaAnim",
    "OpenMayaRender",
    "OpenMaya_v1",
    "OpenMayaUI",
    "MayaEvent",
    "EventManager",
)
