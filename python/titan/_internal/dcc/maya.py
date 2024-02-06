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
    from titan.dcc import Maya
    Maya.cmds...

Either way, these modules are protected from being imported in an environment where Maya is not available.
You can test if Maya is available by checking the "IS_MAYA_AVAILABLE" constant or by calling "Maya.is_available".
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import inspect
import types
from typing import Callable, Optional
import weakref

# Local imports
from titan.qt import QtCore, QtWidgets

EventType = Enum("EventType", ("SceneEvent", "ActionEvent"))
MayaEvent = Enum(
    "MayaEvent",
    (
        "BeforeOpen",
        "BeforeNew",
        "BeforeImport",
        "BeforeExport",
        "BeforeSave",
        "BeforeImportReference",
        "BeforeExportReference",
        "BeforeUnloadReference",
        "BeforeLoadReference",
        "BeforeCreateReference",
        "BeforeRemoveReference",
        "AfterOpen",
        "AfterNew",
        "AfterImport",
        "AfterExport",
        "AfterSave",
        "AfterImportReference",
        "AfterExportReference",
        "AfterUnloadReference",
        "AfterLoadReference",
        "AfterCreateReference",
        "AfterRemoveReference",
        "SelectionChanged",
        "TimeChanged",
        "MayaInitialized",
        "MayaExiting",
        "SceneUpdate",
    ),
)

_EVENT_MAP = {
    MayaEvent.BeforeOpen: ("kBeforeOpen", EventType.SceneEvent),
    MayaEvent.BeforeNew: ("kBeforeNew", EventType.SceneEvent),
    MayaEvent.BeforeImport: ("kBeforeImport", EventType.SceneEvent),
    MayaEvent.BeforeExport: ("kBeforeExport", EventType.SceneEvent),
    MayaEvent.BeforeSave: ("kBeforeSave", EventType.SceneEvent),
    MayaEvent.BeforeImportReference: ("kBeforeImportReference", EventType.SceneEvent),
    MayaEvent.BeforeExportReference: ("kBeforeExportReference", EventType.SceneEvent),
    MayaEvent.BeforeUnloadReference: ("kBeforeUnloadReference", EventType.SceneEvent),
    MayaEvent.BeforeLoadReference: ("kBeforeLoadReference", EventType.SceneEvent),
    MayaEvent.BeforeCreateReference: ("kBeforeCreateReference", EventType.SceneEvent),
    MayaEvent.BeforeRemoveReference: ("kBeforeRemoveReference", EventType.SceneEvent),
    MayaEvent.AfterOpen: ("kAfterOpen", EventType.SceneEvent),
    MayaEvent.AfterNew: ("kAfterNew", EventType.SceneEvent),
    MayaEvent.AfterImport: ("kAfterImport", EventType.SceneEvent),
    MayaEvent.AfterExport: ("kAfterExport", EventType.SceneEvent),
    MayaEvent.AfterSave: ("kAfterSave", EventType.SceneEvent),
    MayaEvent.AfterImportReference: ("kAfterImportReference", EventType.SceneEvent),
    MayaEvent.AfterExportReference: ("kAfterExportReference", EventType.SceneEvent),
    MayaEvent.AfterUnloadReference: ("kAfterUnloadReference", EventType.SceneEvent),
    MayaEvent.AfterLoadReference: ("kAfterLoadReference", EventType.SceneEvent),
    MayaEvent.AfterCreateReference: ("kAfterCreateReference", EventType.SceneEvent),
    MayaEvent.AfterRemoveReference: ("kAfterRemoveReference", EventType.SceneEvent),
    MayaEvent.SelectionChanged: ("SelectionChanged", EventType.ActionEvent),
    MayaEvent.TimeChanged: ("timeChanged", EventType.ActionEvent),
    MayaEvent.MayaInitialized: ("kMayaInitialized", EventType.SceneEvent),
    MayaEvent.MayaExiting: ("kMayaExiting", EventType.SceneEvent),
    MayaEvent.SceneUpdate: ("kSceneUpdate", EventType.SceneEvent),
}


class EventManager(QtCore.QObject):
    """The EventManager class is used to manage Maya events and signals. It is a
    singleton class that provides signals for each Maya event and connects them
    to the appropriate Maya event. This allows you to connect to Maya events
    using signals and slots.
    """

    _INSTANCE = None
    _CALLBACKS = {}

    # Ensurue these signals are available as class attributes
    # before the class is instantiated and super is called or
    # the signals will not be available.
    for event in _EVENT_MAP:
        locals()[event.name] = QtCore.Signal(object)

    def __new__(cls):
        """Create a new instance of the EventManager class. This is a singleton
        class, so it will only create a new instance if one does not already
        exist. Ideally this class should be created using the "instance" method. but
        this __new__ method will safe guard against creating multiple instances."""
        if not cls._INSTANCE:
            cls._INSTANCE = super(EventManager, cls).__new__(cls)
        return cls._INSTANCE

    def __init__(self):
        super(EventManager, self).__init__()

        # Connect the signals to the Maya events
        for event, data in _EVENT_MAP.items():
            maya_event_name, event_type = data

            if event_type == EventType.SceneEvent:
                maya_event = getattr(OpenMaya.MSceneMessage, maya_event_name)
                self._CALLBACKS[event.name] = OpenMaya.MSceneMessage.addCallback(
                    maya_event, getattr(self, event.name).emit
                )

            elif event_type == EventType.ActionEvent:
                self._CALLBACKS[event.name] = OpenMaya.MEventMessage.addEventCallback(
                    maya_event_name, getattr(self, event.name).emit
                )

    @classmethod
    def instance(cls: EventManager) -> EventManager:
        """Return the instance of the EventManager class."""
        if not cls._INSTANCE:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    @classmethod
    def get_event_signal(cls, event: MayaEvent) -> QtCore.Signal:
        """Return the signal for the given event."""
        return getattr(cls.instance(), event.name)


class EventCallback(QtCore.QObject):

    callback_deleted = QtCore.Signal(str)

    def __init__(
        self, event: MayaEvent, callback: Callable, caller_info: inspect.Traceback
    ):
        super(EventCallback, self).__init__()
        self._event = event
        self._callback = weakref.proxy(callback, self.on_callback_deleted)
        self._caller_info = caller_info
        self._paused: bool = False
        self._id = str(id(self))

    def __call__(self, *args, **kwargs):
        if self.callback and not self._paused:
            return self.callback(*args, **kwargs)

    def on_callback_deleted(self, *args, **kwargs) -> None:
        self._callback = None
        self.callback_deleted.emit(self._id)

    def pause(self, state) -> None:
        self._paused = state

    @property
    def callback(self) -> Callable:
        return self._callback

    @property
    def event(self) -> MayaEvent:
        return self._event

    @property
    def callback_id(self) -> str:
        return self._id


class EventCallbackManager:
    """The EventCallbackManager class is used to manage Maya event callbacks. It is a
    singleton class that provides a way to create and manage Maya event callbacks.
    """

    _INSTANCE = None
    _CALLBACKS = {}

    def __new__(cls):
        """Create a new instance of the EventCallbackManager class. This is a singleton
        class, so it will only create a new instance if one does not already
        exist. Ideally this class should be created using the "instance" method. but
        this __new__ method will safe guard against creating multiple instances."""
        if not cls._INSTANCE:
            cls._INSTANCE = super(EventCallbackManager, cls).__new__(cls)
        return cls._INSTANCE

    def __init__(self):
        super(EventCallbackManager, self).__init__()

    @classmethod
    def instance(cls: EventCallbackManager) -> EventCallbackManager:
        """Return the instance of the EventCallbackManager class."""
        if not cls._INSTANCE:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    def register_callback(self, event: MayaEvent, callback: Callable) -> int:
        """Create a new event callback for the given event and callback function.

        Args:
            event (MayaEvent): The event to create a callback for.
            callback (Callable): The callback function to call when the event is triggered.

        Returns:
            int: The ID of the callback.
        """
        previous_frame = inspect.currentframe().f_back
        caller_info = inspect.getframeinfo(previous_frame)
        event_callback = EventCallback(event, callback, caller_info)
        event_callback.callback_deleted.connect(self.remove_callback)
        signal = EventManager.get_event_signal(event)
        signal.connect(event_callback)
        self._CALLBACKS[event_callback.callback_id] = event_callback
        return event_callback.callback_id

    def remove_callback(self, callback_id: str):
        if callback_id in self._CALLBACKS:
            event_callback = self._CALLBACKS[callback_id]
            signal = EventManager.get_event_signal(event_callback.event)
            signal.disconnect(event_callback)
            del self._CALLBACKS[callback_id]
            event_callback.deleteLater()


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
        >>> # Result: <PySide2.QtWidgets.QWidget(0x6000046dc600, name="MayaWindow") at 0x143378800>
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

else:
    cmds = None
    mel = None
    OpenMaya = None
    OpenMayaAnim = None
    OpenMayaRender = None
    OpenMaya_v1 = None
    OpenMayaUI = None
