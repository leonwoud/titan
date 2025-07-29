"""This module provides access to the Maya API and UI in an environment where Maya is available.
It hopes to offer a consistent interface regardless of the Maya version.

For convenience, the following modules are available:
    - cmds: The Maya commands module.
    - mel: The Maya MEL module.
    - OpenMaya: The Maya OpenMaya module.
    - OpenMayaAnim: The Maya OpenMayaAnim module.
    - OpenMayaRender: The Maya OpenMayaRender module.
    - OpenMaya_v1: The Maya OpenMaya (V1) module.

This is so that you can import them directly from this module, like so:
    from titan.dcc.maya import cmds, mel...

Or you can import the Maya module and access them from there:
    from titan.host import Maya
    Maya.cmds...

Either way, these modules are protected from being imported in an environment where Maya is not available.
You can test if Maya is available by checking the "IS_MAYA_AVAILABLE" constant or by calling "Maya.is_available".
"""

from __future__ import annotations

import atexit
import os
import sys
import types
from typing import Any, Optional, TYPE_CHECKING, cast

from .stubs import (
    MayaCmdsProtocol,
    MayaMelProtocol,
    MayaOpenMayaV1Protocol,
    MayaOpenMayaProtocol,
    MayaOpenMayaProtocolExtended,
    MayaOpenMayaAnimProtocol,
    MayaOpenMayaRenderProtocol,
    MayaOpenMayaUIProtocol,
)

# Local imports
from titan.qt import QtWidgets

from titan.logger import get_logger
from titan._internal.host.maya.events import MayaEvent, EventCallbackManager


# Create a logger
LOGGER = get_logger("titan.host.maya.core")


class _MayaAPI:

    def __init__(self):
        self._openmaya_v1: Optional[types.ModuleType] = None
        self._openmaya: Optional[types.ModuleType] = None
        self._openmayaanim: Optional[types.ModuleType] = None
        self._openmayarender: Optional[types.ModuleType] = None
        self._openmayaui: Optional[types.ModuleType] = None

    @property
    def openmaya_v1(self) -> MayaOpenMayaV1Protocol:
        """Return the Maya OpenMaya (V1) module."""
        if not self._openmaya_v1:
            import maya.OpenMaya as openmaya  # type: ignore

            self._openmaya_v1 = openmaya
        return cast(MayaOpenMayaV1Protocol, self._openmaya_v1)

    @property
    def openmaya(self) -> MayaOpenMayaProtocolExtended:
        """Return the Maya OpenMaya module."""
        if not self._openmaya:
            import maya.api.OpenMaya as openmaya  # type: ignore

            self._openmaya = openmaya
        return cast(MayaOpenMayaProtocolExtended, self._openmaya)

    @property
    def openmayaanim(self) -> MayaOpenMayaAnimProtocol:
        """Return the Maya OpenMayaAnim module."""
        if not self._openmayaanim:
            import maya.OpenMayaAnim as openmayaanim  # type: ignore

            self._openmayaanim = openmayaanim
        return cast(MayaOpenMayaAnimProtocol, self._openmayaanim)

    @property
    def openmayarender(self) -> MayaOpenMayaRenderProtocol:
        """Return the Maya OpenMayaRender module."""
        if not self._openmayarender:
            import maya.OpenMayaRender as openmayarender  # type: ignore

            self._openmayarender = openmayarender
        return cast(MayaOpenMayaRenderProtocol, self._openmayarender)

    @property
    def openmayaui(self) -> MayaOpenMayaUIProtocol:
        """Return the Maya OpenMayaUI module."""
        if not self._openmayaui:
            import maya.OpenMayaUI as openmayaui  # type: ignore

            self._openmayaui = openmayaui
        return cast(MayaOpenMayaUIProtocol, self._openmayaui)


class _MayaUI:
    """This class is used to provide access to the Maya UI module without
    importing it until it is actually needed and provides protection when
    not in Maya."""

    def __init__(self):
        # TODO: logger, so we can track when this module is first imported
        self._window: Optional[QtWidgets.QMainWindow] = None
        self._mqtutil: Optional[types.ModuleType] = None
        self._is_available: Optional[bool] = None

    @property
    def mqtutil(self) -> Any:
        """Return the Maya Qt utility module (maya.OpenMayaUI.MQtUtil)"""
        if not self._mqtutil:
            from maya.OpenMayaUI import MQtUtil  # type: ignore

            self._mqtutil = MQtUtil
        return cast(Any, self._mqtutil)

    @property
    def main_window(self) -> Optional[QtWidgets.QMainWindow]:
        """Return the Maya main window as a QMainWindow."""
        if not self._window:
            from titan.qt import QtWidgets, wrap_instance

            ptr = self.mqtutil.mainWindow()
            if ptr is not None:
                self._window = cast(
                    QtWidgets.QMainWindow,
                    wrap_instance(int(ptr), QtWidgets.QMainWindow),
                )
        return self._window

    @property
    def is_available(self) -> bool:
        """Return True if Maya UI is available."""
        if self._is_available is None:
            from titan.host.maya import Maya

            if Maya.is_available:
                self._is_available = not Maya.cmds.about(batch=True)
            else:
                self._is_available = False
        return self._is_available

    @classmethod
    def find_window(
        cls, window_name, object_type=QtWidgets.QWidget
    ) -> Optional[QtWidgets.QWidget]:
        """Find a window by name and return it as an instance of "object_type".

        Args:
            window_name (str): The name of the window to find.
            object_type (type): The type to return the window as.

        Returns:
            Optional[object_type]: The window as an instance of "object_type" if found.
        """
        from titan.qt import wrap_instance

        ptr = cast(Any, cls.mqtutil).findWindow(window_name)
        if ptr is not None:
            return cast(Any, wrap_instance(int(ptr), object_type))

    @classmethod
    def find_control(
        cls, control_name, object_type=QtWidgets.QWidget
    ) -> Optional[QtWidgets.QWidget]:
        """Find a control by name and return it as an instance of "object_type".

        Args:
            control_name (str): The name of the control to find.
            object_type (type): The type to return the control as.

        Returns:
            Optional[object_type]: The control as an instance of "object_type" if found.
        """
        from titan.qt import wrap_instance

        ptr = cast(Any, cls.mqtutil).findControl(control_name)
        if ptr is not None:
            return cast(Any, wrap_instance(int(ptr), object_type))


class _MayaCore(type):

    def __init__(self, *args, **kwargs):
        # TODO: logger, so we can track when this module is first imported
        self._cmds: Optional[types.ModuleType] = None
        self._mel: Optional[types.ModuleType] = None
        self._ui: Optional[_MayaUI] = None
        self._api: Optional[_MayaAPI] = None
        self._events = MayaEvent
        self._event_manager: Optional[EventCallbackManager] = None
        self._is_standalone: Optional[bool] = None
        self._is_available: Optional[bool] = None
        atexit.register(self._cleanup)

    @property
    def cmds(self) -> MayaCmdsProtocol:
        """Return the Maya commands module."""
        if self._cmds is None:
            try:
                import maya.cmds as cmds # type: ignore

                self._cmds = cmds
            except ImportError:
                raise ImportError("Maya cmds module not available")
        return cast(MayaCmdsProtocol, self._cmds)

    @property
    def mel(self) -> MayaMelProtocol:
        """Return the Maya MEL module."""
        if self._mel is None:
            try:
                import maya.mel as mel # type: ignore

                self._mel = mel
            except ImportError:
                raise ImportError("Maya mel module not available")
        return cast(MayaMelProtocol, self._mel)

    @property
    def api(self) -> _MayaAPI:
        """Return the Maya API module."""
        if self._api is None:
            self._api = _MayaAPI()
        return self._api

    @property
    def ui(self) -> _MayaUI:
        """Return the Maya UI module."""
        if self._ui is None:
            self._ui = _MayaUI()
        return self._ui

    @property
    def is_standalone(self) -> bool:
        """Return True if Maya is running in mayapy."""
        if self._is_standalone is None:
            self._is_standalone = "mayapy" in os.path.basename(sys.executable).lower()
        return self._is_standalone

    @property
    def is_initialized(self) -> bool:
        """Return True if Maya is initialized."""
        try:
            self.cmds.about(apiVersion=True)
            return True
        except AttributeError:
            return False

    @property
    def is_available(self) -> bool:
        """Return True if the maya api is available.

        This returns True in a standalone or interactive Maya session.
        """
        if self._is_available is None:
            if self.is_standalone:
                self._is_available = True
            elif "maya" in os.path.basename(sys.executable).lower():
                self._is_available = True
            else:
                self._is_available = False
        return self._is_available

    @property
    def events(self) -> MayaEvent:
        """Return the MayaEvent enum."""
        return cast(MayaEvent, self._events)

    @property
    def event_manager(self) -> EventCallbackManager:
        """Return the EventCallbackManager instance."""
        if not self._event_manager:
            self._event_manager = EventCallbackManager.instance()
        return self._event_manager

    def initialize(self):
        """Initialize the Maya host.

        Raises:
            RuntimeError: If Maya is not available.
        """
        if not self.is_available:
            raise RuntimeError("Maya is not available")

        if self.is_standalone and not self.is_initialized:
            import maya.standalone # type: ignore

            maya.standalone.initialize()
            self._is_standalone = True
            self._is_available = True
            LOGGER.info("Maya standalone initialized")

    def _cleanup(self):
        """Cleanup the Maya host."""
        self._cmds = None
        self._mel = None
        self._ui = None
        self._api = None
        self._events = None
        self._event_manager = None

        if self.is_standalone and self.is_initialized:
            import maya.standalone # type: ignore

            maya.standalone.uninitialize()
            LOGGER.info("Maya standalone uninitialized")
