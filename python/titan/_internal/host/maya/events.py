from __future__ import annotations

from enum import Enum
import inspect
import types
from typing import Any, Callable, Optional, TYPE_CHECKING, Union, cast
import weakref

from .stubs import MayaOpenMayaProtocolExtended

# Local imports
from titan.logger import get_logger
from titan.qt import QtCore

# Create a logger
LOGGER_NAME = "titan.host.maya.events"


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

    # Ensure these signals are available as class attributes
    # before the class is instantiated and super is called or
    # the signals will not be available.
    # Note: Dynamic signal creation - PyLance can't type-check this,
    # but signals will be available as attributes at runtime
    for maya_event in _EVENT_MAP:
        locals()[maya_event.name] = QtCore.Signal(object)  # type: ignore

    def __init__(self):
        super().__init__()
        from titan.host.maya import OpenMaya  # Avoid cyclic import

        # Check if Maya is available
        if OpenMaya is None:
            raise RuntimeError(
                "Maya OpenMaya module is not available. "
                "MayaEventManager can only be used within a Maya environment."
            )

        # Cast OpenMaya to our extended protocol for better typing
        openmaya = cast(MayaOpenMayaProtocolExtended, OpenMaya)

        # Connect the signals to the Maya events
        for maya_event, data in _EVENT_MAP.items():
            maya_event_name, event_type = data

            if event_type == EventType.SceneEvent:
                maya_event_constant = getattr(openmaya.MSceneMessage, maya_event_name)
                signal_emit = cast(
                    Callable[..., Any], getattr(self, maya_event.name).emit
                )
                self._CALLBACKS[maya_event.name] = openmaya.MSceneMessage.addCallback(
                    maya_event_constant, signal_emit
                )

            elif event_type == EventType.ActionEvent:
                signal_emit = cast(
                    Callable[..., Any], getattr(self, maya_event.name).emit
                )
                self._CALLBACKS[maya_event.name] = (
                    openmaya.MEventMessage.addEventCallback(
                        maya_event_name, signal_emit
                    )
                )

    @classmethod
    def instance(cls) -> MayaEventManager:
        """Return the instance of the EventManager class."""
        if not cls._INSTANCE:
            try:
                cls._INSTANCE = cls()
            except RuntimeError as e:
                raise RuntimeError(f"Cannot create MayaEventManager: {e}")
        return cls._INSTANCE

    @classmethod
    def get_event_signal(cls, event: MayaEvent) -> QtCore.SignalInstance:
        """Return the signal for the given event."""
        return cast(QtCore.SignalInstance, getattr(cls.instance(), event.name))


class EventCallback(QtCore.QObject):
    """The EventCallback class is used to create a callback for a Maya event.
    When the Maya event is triggered via MSceneMessage or MEventMessage, the callback
    will be called. The callback can be any callable object, such as a function,
    method, or lambda. The callback can also hold client data, which can be used to
    pass data to the callback when it is called.

    It also holds a reference to the caller info, so that it can be used to debug / track
    usage of the callback.

    Signals:
        callback_deleted: A signal that is emitted when the callback is deleted.
    """

    callback_deleted = QtCore.Signal(str)

    def __init__(
        self,
        event: MayaEvent,
        callback: Callable[..., Any],
        caller_info: Optional[Union[inspect.FrameInfo, inspect.Traceback]],
        client_data: Any,
    ):
        super().__init__()
        self._event = event
        self._callback_name = callback.__name__
        if isinstance(callback, types.MethodType):
            class_name = callback.__self__.__class__.__name__
            self._callback_name = f"{class_name}.{self._callback_name}"
            self._callback = weakref.WeakMethod(callback, self.on_callback_deleted)
        else:
            self._callback = weakref.ref(callback, self.on_callback_deleted)
        self._caller_info = caller_info
        self._enabled_state: bool = True
        self._id: str = str(id(self))
        self._client_data = client_data

    def __call__(self, *args, **kwargs):
        if self.callback is not None and self.is_enabled:
            dereferenced_cb = self.callback()
            if dereferenced_cb is not None:
                if self._client_data is not None:
                    return dereferenced_cb(self._client_data)
                return dereferenced_cb()

    @QtCore.Slot()
    def on_callback_deleted(self, _: weakref.ref) -> None:
        """A slot that is called when the callback is deleted. This will emit the
        callback_deleted signal."""
        self._callback = None
        self.callback_deleted.emit(self._id)

    def set_enabled_state(self, state: bool) -> None:
        """Set the enabled state of the callback."""
        self._enabled_state = state

    @property
    def is_enabled(self):
        """Return the enabled state of the callback."""
        return self._enabled_state

    @property
    def callback(self) -> Optional[Union[weakref.ref, weakref.WeakMethod]]:
        """Return the callback function."""
        return self._callback

    @property
    def maya_event(self) -> MayaEvent:
        """Return the Maya event that the callback is connected to."""
        return self._event

    @property
    def callback_id(self) -> str:
        """Return the ID of the callback."""
        return self._id

    @property
    def callback_name(self) -> str:
        """Return the name of the callback."""
        return self._callback_name


class EventCallbackManager:
    """The EventCallbackManager class is used to manage Maya event callbacks. It is a
    singleton class that provides a way to create and manage Maya event callbacks.
    """

    _INSTANCE = None
    _CALLBACKS = {}

    def __init__(self):
        super().__init__()

    @classmethod
    def instance(cls) -> EventCallbackManager:
        """Return the instance of the EventCallbackManager class."""
        if not cls._INSTANCE:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    def register_callback(
        self,
        event: MayaEvent,
        callback: Callable[..., Any],
        client_data: Optional[Any] = None,
    ) -> str:
        """Create a new event callback for the given event and callback function.

        Args:
            event (MayaEvent): The event to create a callback for.
            callback (Callable): The callback function to call when the event is triggered.
            client_data (Any): The client data to pass to the callback function.

        Returns:
            str: The ID of the callback.
        """
        current_frame = inspect.currentframe()
        caller_info = None
        if current_frame:
            previous_frame = cast(types.FrameType, current_frame.f_back)
            caller_info = inspect.getframeinfo(previous_frame)
        event_callback = EventCallback(event, callback, caller_info, client_data)
        event_callback.callback_deleted.connect(self.remove_callback)
        signal = MayaEventManager.get_event_signal(event)
        signal.connect(event_callback)
        self._CALLBACKS[event_callback.callback_id] = event_callback
        log = get_logger(LOGGER_NAME)
        log.debug("%s callback %s registered.", event, event_callback.callback_name)
        return event_callback.callback_id

    def remove_callback(self, callback_id: str) -> None:
        """Remove the callback with the given ID.

        Args:
            callback_id (str): The ID of the callback to remove.
        """
        if callback_id in self._CALLBACKS:
            event_callback = self._CALLBACKS[callback_id]
            log = get_logger(LOGGER_NAME)
            log.debug(
                "%s callback %s removed.",
                event_callback.maya_event,
                event_callback.callback_name,
            )
            signal = MayaEventManager.get_event_signal(event_callback.maya_event)
            signal.disconnect(event_callback)
            del self._CALLBACKS[callback_id]
            event_callback.deleteLater()
