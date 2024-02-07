from __future__ import annotations

from enum import Enum
import inspect
from typing import Any, Callable, Optional
import weakref

# Local imports
from titan.qt import QtCore


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


class MayaEventManager(QtCore.QObject):
    """The MayaEventManager class is used to convert Maya events into Qt signals.
    This allows the connection of Maya events to Qt's signals and slots.
    """

    _INSTANCE = None
    _CALLBACKS = {}

    # Ensurue these signals are available as class attributes
    # before the class is instantiated and super is called or
    # the signals will not be available.
    for event in _EVENT_MAP:
        locals()[event.name] = QtCore.Signal(object)

    def __new__(cls):
        """Create a new instance of the MayaEventManager class. This is a singleton
        class, so it will only create a new instance if one does not already
        exist. Ideally this class should be created using the "instance" method. but
        this __new__ method will safe guard against creating multiple instances."""
        if not cls._INSTANCE:
            cls._INSTANCE = super(MayaEventManager, cls).__new__(cls)
        return cls._INSTANCE

    def __init__(self):
        super(MayaEventManager, self).__init__()
        from titan._internal.vendor.maya import OpenMaya  # Avoid cyclic import

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
    def instance(cls: MayaEventManager) -> MayaEventManager:
        """Return the instance of the EventManager class."""
        if not cls._INSTANCE:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    @classmethod
    def get_event_signal(cls, event: MayaEvent) -> QtCore.Signal:
        """Return the signal for the given event."""
        return getattr(cls.instance(), event.name)


class EventCallback(QtCore.QObject):

    """The EventCallback class is used to create a callback for a Maya event. It is a
    QObject so that it can be connected to a Maya event signal. When the event is
    triggered, the callback will be called.
    
    It also holds reference to the caller info, so that it can be used to debug / track
    usage of the callback."""

    callback_deleted = QtCore.Signal(str)

    def __init__(
        self, event: MayaEvent, callback: Callable, caller_info: inspect.Traceback, client_data: Any
    ):
        super(EventCallback, self).__init__()
        self._event = event
        self._callback = weakref.proxy(callback, self.on_callback_deleted)
        self._caller_info = caller_info
        self._paused: bool = False
        self._id = str(id(self))
        self._client_data = client_data

    def __call__(self):
        if self.callback and not self._paused:
            if self._client_data is not None:
                return self.callback(self._client_data)
            return self.callback()

    @QtCore.Slot()
    def on_callback_deleted(self) -> None:
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

    def register_callback(self, event: MayaEvent, callback: Callable, client_data: Optional[Any] = None) -> int:
        """Create a new event callback for the given event and callback function.

        Args:
            event (MayaEvent): The event to create a callback for.
            callback (Callable): The callback function to call when the event is triggered.
            client_data (Any): The client data to pass to the callback function.

        Returns:
            int: The ID of the callback.
        """
        previous_frame = inspect.currentframe().f_back
        caller_info = inspect.getframeinfo(previous_frame)
        event_callback = EventCallback(event, callback, caller_info, client_data)
        event_callback.callback_deleted.connect(self.remove_callback)
        signal = MayaEventManager.get_event_signal(event)
        signal.connect(event_callback)
        self._CALLBACKS[event_callback.callback_id] = event_callback
        return event_callback.callback_id

    def remove_callback(self, callback_id: str):
        if callback_id in self._CALLBACKS:
            event_callback = self._CALLBACKS[callback_id]
            signal = MayaEventManager.get_event_signal(event_callback.event)
            signal.disconnect(event_callback)
            del self._CALLBACKS[callback_id]
            event_callback.deleteLater()