"""Type protocols for preferences to provide typing support for dynamic attributes."""

from __future__ import annotations


from typing import Any, Optional, Protocol


# Protocol for components with value property
class ValueComponent(Protocol):
    @property
    def value(self) -> Any: ...
    @value.setter
    def value(self, val: Any) -> None: ...


# Protocol for color components (specific to logger)
class ColorComponent(Protocol):
    @property
    def value(self) -> Any: ...


# Protocol for logger color group
class LoggerColors(Protocol):
    @property
    def critical(self) -> ColorComponent: ...
    @property
    def error(self) -> ColorComponent: ...
    @property
    def warning(self) -> ColorComponent: ...
    @property
    def info(self) -> ColorComponent: ...
    @property
    def debug(self) -> ColorComponent: ...
    @property
    def trace(self) -> ColorComponent: ...


# Protocol for position group (window preferences)
class PositionGroup(Protocol):
    @property
    def x(self) -> ValueComponent: ...
    @property
    def y(self) -> ValueComponent: ...


# Protocol for window group
class WindowGroup(Protocol):
    @property
    def width(self) -> ValueComponent: ...
    @property
    def height(self) -> ValueComponent: ...
    @property
    def pos(self) -> PositionGroup: ...


# Protocol for logger preferences structure
class LoggerPreferences(Protocol):
    @property
    def level(self) -> ValueComponent: ...  # Changed from Component to ValueComponent
    @property
    def colors(self) -> LoggerColors: ...


# Protocol for preferences with window settings
class WindowPreferences(Protocol):
    @property
    def win(self) -> WindowGroup: ...
    def get_component(self, path: str) -> Optional[Any]: ...


# Export commonly used protocols
__all__ = ["LoggerPreferences", "WindowPreferences", "ColorComponent", "ValueComponent"]
