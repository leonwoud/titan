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

import types
from typing import Optional

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
    def openmaya_v1(self) -> types.ModuleType:
        """Return the Maya OpenMaya (V1) module."""
        if not self._openmaya_v1:
            import maya.OpenMaya as openmaya

            self._openmaya_v1 = openmaya
        return self._openmaya_v1

    @property
    def openmaya(self) -> types.ModuleType:
        """Return the Maya OpenMaya module."""
        if not self._openmaya:
            import maya.api.OpenMaya as openmaya

            self._openmaya = openmaya
        return self._openmaya

    @property
    def openmayaanim(self) -> types.ModuleType:
        """Return the Maya OpenMayaAnim module."""
        if not self._openmayaanim:
            import maya.OpenMayaAnim as openmayaanim

            self._openmayaanim = openmayaanim
        return self._openmayaanim

    @property
    def openmayarender(self) -> types.ModuleType:
        """Return the Maya OpenMayaRender module."""
        if not self._openmayarender:
            import maya.OpenMayaRender as openmayarender

            self._openmayarender = openmayarender
        return self._openmayarender

    @property
    def openmayaui(self) -> types.ModuleType:
        """Return the Maya OpenMayaUI module."""
        if not self._openmayaui:
            import maya.OpenMayaUI as openmayaui

            self._openmayaui = openmayaui
        return self._openmayaui


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
    def mqtutil(self) -> types.ModuleType:
        """Return the Maya Qt utility module (maya.OpenMayaUI.MQtUtil)"""
        if not self._mqtutil:
            from maya.OpenMayaUI import MQtUtil

            self._mqtutil = MQtUtil
        return self._mqtutil

    @property
    def main_window(self) -> QtWidgets.QMainWindow:
        """Return the Maya main window as a QMainWindow."""
        if not self._window:
            from titan.qt import QtWidgets, wrap_instance

            ptr = self.mqtutil.mainWindow()
            if ptr is not None:
                self._window = wrap_instance(int(ptr), QtWidgets.QMainWindow)
        return self._window

    @property
    def is_available(self) -> bool:
        """Return True if Maya UI is available."""
        if not self._is_available:
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

        ptr = cls.mqtutil.findWindow(window_name)
        if ptr:
            return wrap_instance(int(ptr), object_type)

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

        ptr = cls.mqtutil.findControl(control_name)
        if ptr:
            return wrap_instance(int(ptr), object_type)


class _MayaCore(type):

    def __init__(cls, *args, **kwargs):
        # TODO: logger, so we can track when this module is first imported
        cls._cmds: Optional[types.ModuleType] = None
        cls._mel: Optional[types.ModuleType] = None
        cls._ui: Optional[_MayaUI] = None
        cls._api: Optional[_MayaAPI] = None
        cls._events: MayaEvent = MayaEvent
        cls._event_manager: Optional[EventCallbackManager] = None
        cls._is_standalone: Optional[bool] = None
        cls._is_available: Optional[bool] = None

    @property
    def cmds(self) -> types.ModuleType:
        """Return the Maya commands module."""
        if self._cmds is None:
            try:
                import maya.cmds as cmds
            except ImportError:
                cmds = None
            self._cmds = cmds
        return self._cmds

    @property
    def mel(self) -> types.ModuleType:
        """Return the Maya MEL module."""
        if self._mel is None:
            try:
                import maya.mel as mel
            except ImportError:
                mel = None
            self._mel = mel
        return self._mel

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
        """Return True if Maya is running in batch mode."""
        if self._is_standalone is None:
            self._is_standalone = self.cmds.about(batch=True)
        return self._is_standalone

    @property
    def is_available(self) -> bool:
        """Return True if Maya is available."""
        if self._is_available is None:
            if not self.cmds:
                self._is_available = False
            else:
                # Catch the case where the cmds module is stubbed in
                # the current environment.
                try:
                    self.cmds.about(batch=True)
                    self._is_available = True
                except AttributeError:
                    self._is_available = False
        return self._is_available

    @property
    def events(self) -> MayaEvent:
        """Return the MayaEvent enum."""
        return self._events

    @property
    def event_manager(self) -> EventCallbackManager:
        """Return the EventCallbackManager instance."""
        if not self._event_manager:
            self._event_manager = EventCallbackManager.instance()
        return self._event_manager
