"""Type stubs for Maya APIs to provide typing support without requiring Maya installation."""

from __future__ import annotations

from typing import Any, Callable, Optional, Protocol


# Maya cmds module protocol
class MayaCmdsProtocol(Protocol):
    """Protocol for maya.cmds module."""
    
    def about(self, apiVersion: bool = False, batch: bool = False, **kwargs: Any) -> Any: ...
    def ls(self, *args: Any, **kwargs: Any) -> list[str]: ...
    def select(self, *args: Any, **kwargs: Any) -> None: ...


# Maya mel module protocol  
class MayaMelProtocol(Protocol):
    """Protocol for maya.mel module."""
    
    def eval(self, command: str) -> Any: ...


# Maya OpenMaya v1 protocol
class MayaOpenMayaV1Protocol(Protocol):
    """Protocol for maya.OpenMaya module."""
    
    class MObject: ...
    class MDagPath: ...
    class MSelectionList: ...

# Maya OpenMaya v2 protocol
class MayaOpenMayaProtocol(Protocol):
    """Protocol for maya.api.OpenMaya module."""
    
    class MObject: ...
    class MDagPath: ...  
    class MSelectionList: ...

# Maya OpenMayaUI module protocol
class MayaOpenMayaUIProtocol(Protocol):
    """Protocol for maya.OpenMayaUI module."""
    
    class MQtUtil:
        @staticmethod
        def mainWindow() -> Optional[int]: ...
        @staticmethod
        def findWindow(name: str) -> Optional[int]: ...
        @staticmethod
        def findControl(name: str) -> Optional[int]: ...


# Maya OpenMayaAnim module protocol
class MayaOpenMayaAnimProtocol(Protocol):
    """Protocol for maya.OpenMayaAnim module."""
    
    class MAnimControl: ...
    # Add more animation classes as needed


# Maya OpenMayaRender module protocol
class MayaOpenMayaRenderProtocol(Protocol):
    """Protocol for maya.OpenMayaRender module."""
    
    class MRenderer: ...
    # Add more render classes as needed


# Maya Message APIs for events
class MSceneMessageProtocol(Protocol):
    """Protocol for maya.api.OpenMaya.MSceneMessage."""
    
    @staticmethod
    def addCallback(message: Any, callback: Callable[..., Any]) -> Any: ...
    
    # Scene message constants
    kBeforeOpen: Any
    kBeforeNew: Any
    kBeforeImport: Any
    kBeforeExport: Any
    kBeforeSave: Any
    kBeforeImportReference: Any
    kBeforeExportReference: Any
    kBeforeUnloadReference: Any
    kBeforeLoadReference: Any
    kBeforeCreateReference: Any
    kBeforeRemoveReference: Any
    kAfterOpen: Any
    kAfterNew: Any
    kAfterImport: Any
    kAfterExport: Any
    kAfterSave: Any
    kAfterImportReference: Any
    kAfterExportReference: Any
    kAfterUnloadReference: Any
    kAfterLoadReference: Any
    kAfterCreateReference: Any
    kAfterRemoveReference: Any
    kMayaInitialized: Any
    kMayaExiting: Any
    kSceneUpdate: Any


class MEventMessageProtocol(Protocol):
    """Protocol for maya.api.OpenMaya.MEventMessage."""
    
    @staticmethod
    def addEventCallback(event: str, callback: Callable[..., Any]) -> Any: ...


# Updated OpenMaya protocol to include message classes
class MayaOpenMayaProtocolExtended(MayaOpenMayaProtocol):
    """Extended OpenMaya protocol with message classes."""
    
    MSceneMessage: MSceneMessageProtocol
    MEventMessage: MEventMessageProtocol