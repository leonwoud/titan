from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Generic, Optional, Type, TypeVar, Union, cast, overload

from titan.types import get_data_type
from titan.qt import QtCore, QtGui

from .parser import PreferenceNode

if TYPE_CHECKING:
    from .main import Preferences

Number = Union[int, float]
DataTypes = Union[str, float, int, bool]
T = TypeVar("T")


class Group:
    """Represents a group of components.

    Implicitly builds a group path based on the attribute access pattern.

    Example:
        Create a group with two components:
            general = Group("general")
            general.appearance.add_component(ColorPicker("BackgroundColor", "#FFFFFF"))
            general.appearance.add_component(ColorPicker("TextColor", "#000000"))

        Components can be accessed like this:
            general.appearance.BackgroundColor
            general.appearance.TextColor
    """

    def __init__(self, name: str):
        self._name = name
        self._components = {}

    def __getattr__(self, name: str) -> Component:
        # Check if this is accessing a component that was added
        if name in self._components:
            return self._components[name]
        # Otherwise create a new Group, but type it as Component for PyLance
        obj = Group(name)
        self.__dict__[name] = obj
        return obj  # type: ignore

    def add_component(self, component: Component) -> None:
        """Add a component to the group, ensure the component name is unique.
        Args:
            component: The component to add.

        Raises:
            ValueError: If a component with the same name already exists."""
        if component.name in self._components:
            raise ValueError(f"Component with name {component.name} already exists.")
        self._components[component.name] = component
        self.__dict__[component.name] = component


class Component(Generic[T]):

    _TYPE: Optional[Enum] = None

    Type = Enum("ComponentType", "Settings Field State Color Combo Radio Slider")

    def __init__(self, name: str, path: str, label: Optional[str] = None):
        self.name = name
        self.path = path
        self.label = label
        self.preferences: Preferences
        self.default: Optional[T] = None

    @classmethod
    def validate(cls, node: PreferenceNode):
        """Validate the preference node contains the required attributes for this
        component and/or create the missing attributes if applicable."""
        # Label is optional, if it does not exist, we will default to an empty str
        if not hasattr(node, "label"):
            node.add_property("label", "")

        if not hasattr(node, "name"):
            raise ValueError(
                f"{node.node_type} ({node.name}) node must have a name attribute."
            )
        if not hasattr(node, "default"):
            raise ValueError(
                f"{node.node_type} ({node.name}) must have a default attribute."
            )
        if node.default == "null":
            setattr(node, "default", None)

    @classmethod
    @abstractmethod
    def from_preference_node(cls, node: PreferenceNode) -> Component:
        """Create a component from a preference node."""
        cls.validate(node)

    def set_preferences(self, preferences: Preferences) -> None:
        """Set the preferences object for this component."""
        self.preferences = preferences

    @property
    def value(self) -> Optional[T]:
        """Get the value from the preferences."""
        out = self.preferences.get_value(self.path)
        if out is None:
            out = self.default
        return cast(Optional[T], out)

    @value.setter
    def value(self, in_val: DataTypes) -> None:
        """Set the value in the preferences."""
        self.preferences.set_value(self.path, in_val)

    @property
    def type(self):
        return self._TYPE


class TypedComponent(Component):

    def __init__(
        self, name: str, path: str, data_type: str, label: Optional[str] = None
    ):
        super().__init__(name, path, label)
        self.data_type = cast(Type[DataTypes], get_data_type(data_type))

    @property
    def value(self) -> Optional[DataTypes]:
        """Get the value from the preferences."""
        out = self.preferences.get_value(self.path)
        if out is None:
            out = self.default
        if out is not None:
            # Handle empty strings for numeric types
            if isinstance(out, str) and out == "" and self.data_type in (int, float):
                return None
            return self.data_type(out)

    @value.setter
    def value(self, in_val: DataTypes) -> None:
        """Set the value in the preferences."""
        self.preferences.set_value(self.path, in_val)


class Settings(Component):

    _TYPE = Component.Type.Settings

    def __init__(self, name, scope, application, organization):
        super().__init__(name, "", None)
        self.scope = self._get_scope(scope)
        self.application = application
        self.organization = organization

    @staticmethod
    def _get_scope(scope: str) -> QtCore.QSettings.Scope:
        """Get the QSettings scope from a string."""
        if "UserScope" in scope:
            return QtCore.QSettings.Scope.UserScope
        if "SystemScope" in scope:
            return QtCore.QSettings.Scope.SystemScope
        raise AttributeError("Invalid scope")

    @classmethod
    def validate(cls, node: PreferenceNode):

        # Add the scope attribute if it does not exist, we will default to UserScope
        if not hasattr(node, "scope"):
            node.add_property("scope", "QtCore.QSettings.UserScope")

        # Try to get the scope attribute, if it fails, raise an error
        try:
            cls._get_scope(node.scope)
        except AttributeError:
            raise ValueError(f"Invalid QSettings scope attribute: {node.scope}")

        if not hasattr(node, "application"):
            raise ValueError(
                "Settings '{node.name}' must have an application attribute."
            )

        if not hasattr(node, "organization"):
            raise ValueError(
                "Settings '{node.name}' must have an organization attribute."
            )

    @classmethod
    def from_preference_node(cls, node: PreferenceNode) -> Settings:
        # default and name properties aren't needed for the Settings component
        # If they're not given, it shouldn't fail.
        if not hasattr(node, "default"):
            node.add_property("default", "")
        if not hasattr(node, "name"):
            node.add_property("name", "")
        super(Settings, cls).from_preference_node(node)
        return cls(node.name, node.scope, node.application, node.organization)


class Field(TypedComponent):

    _TYPE = Component.Type.Field

    def __init__(
        self,
        name: str,
        path: str,
        data_type: str,
        default: str,
        range_: Optional[tuple[str, str]] = None,
        label: Optional[str] = None,
    ):
        super().__init__(name, path, data_type, label=label)
        self.data_type = cast(Type[DataTypes], get_data_type(data_type))
        if default and default.strip():
            self.default = self.data_type(default)
        else:
            # For numeric types, use None instead of empty string
            if self.data_type in (int, float):
                self.default = None
            else:
                self.default = ""
        self.range = tuple(self.data_type(i) for i in range_) if range_ else None

    @classmethod
    def validate(cls, node: PreferenceNode):
        super(Field, cls).validate(node)
        if not hasattr(node, "type"):
            raise ValueError(f"Field '{node.name}' must have a type attribute.")

        # Validate we can convert the default value to the specified data type
        if node.default:
            data_type = cast(Type[DataTypes], get_data_type(node.type))
            try:
                data_type(node.default)
            except ValueError:
                raise ValueError(f"Invalid default value for field {node.name}")

    @classmethod
    def from_preference_node(cls, node: PreferenceNode):
        super(Field, cls).from_preference_node(node)
        if hasattr(node, "range"):
            range_ = tuple([i for i in node.range.split(" ")])
        else:
            range_ = None
        return cls(
            node.name,
            node.get_path(),
            node.type,
            cast(str, node.default),
            range_=cast(tuple[str, str], range_),
            label=node.label,
        )


class State(Component[bool]):

    _TYPE = Component.Type.State

    def __init__(self, name: str, path: str, default: str, label: Optional[str] = None):
        super().__init__(name, path, label=label)
        self.default = as_bool(default)

    @classmethod
    def from_preference_node(cls, node: PreferenceNode):
        super(State, cls).from_preference_node(node)
        return cls(
            node.name, node.get_path(), cast(str, node.default), label=node.label
        )

    @property
    def value(self) -> bool:
        """Get the value from the preferences."""
        value = cast(bool, self.preferences.get_value(self.path))
        if value is None:
            value = self.default if self.default is not None else False
        return as_bool(value)

    @value.setter
    def value(self, in_val: DataTypes) -> None:
        """Set the value in the preferences."""
        self.preferences.set_value(self.path, in_val)


class Color(Component[Union[QtGui.QColor, str]]):

    _TYPE = Component.Type.Color

    def __init__(self, name: str, path: str, default: str, label: Optional[str] = None):
        super().__init__(name, path, label=label)
        self.default = default

    @classmethod
    def from_preference_node(cls, node: PreferenceNode):
        super(Color, cls).from_preference_node(node)
        # Add the alpha component if not included
        default_val = cast(str, node.default)
        default = [comp.strip() for comp in default_val.split(",")]
        if len(default) == 3:
            default.append("255")
        return cls(node.name, node.get_path(), ",".join(default), node.label)

    @property
    def value(self) -> Optional[QtGui.QColor]:
        """Get the color from the preferences."""
        value = self.preferences.get_value(self.path)
        if value is None:
            value = self.default
        return QtGui.QColor(
            *[int(comp.strip()) for comp in cast(str, value).split(",")]
        )

    @value.setter
    def value(self, in_val: DataTypes) -> None:
        """Set the value in the preferences."""
        self.preferences.set_value(self.path, in_val)


class TypedItemComponent(TypedComponent):
    """A shared base class for components that contain items."""

    def __init__(
        self,
        name: str,
        path: str,
        data_type: str,
        items: list[str],
        default: str,
        label: Optional[str] = None,
    ):
        super().__init__(name, path, data_type, label=label)
        self.default = self.data_type(default)
        self._items = []
        for item in items:
            self._items.append(self.data_type(item))

    def items(self) -> list:
        return [item for item in self._items]

    @classmethod
    def validate(cls, node: PreferenceNode):
        super(TypedItemComponent, cls).validate(node)
        if not node.children:
            raise ValueError(
                f"{cls.__name__} '{node.name}' node must have at least one item"
            )
        if not hasattr(node, "type"):
            raise ValueError(
                f"{cls.__name__} '{node.name}' node must have a type attribute."
            )

        # Validate we can convert the default value to the specified data type
        data_type = cast(Type[DataTypes], get_data_type(node.type))
        if node.default:
            try:
                data_type(node.default)
            except ValueError:
                raise ValueError(
                    f"Invalid default value for {cls.__name__} '{node.name}'"
                )

    @classmethod
    def from_preference_node(cls, node: PreferenceNode):
        super(TypedItemComponent, cls).from_preference_node(node)
        items = [child.name for child in node.children]
        return cls(
            node.name,
            node.get_path(),
            node.type,
            items,
            cast(str, node.default),
            label=node.label,
        )


class Combo(TypedItemComponent):
    """A combo box component."""

    _TYPE = Component.Type.Combo


class Radio(TypedItemComponent):
    """A radio button component."""

    _TYPE = Component.Type.Radio


class Slider(TypedComponent):
    """A slider component."""

    _TYPE = Component.Type.Slider

    def __init__(
        self,
        name: str,
        path: str,
        data_type: str,
        default: str,
        step: str,
        range_: tuple[str, str],
        field: str,  # none, left, right
        label: Optional[str] = None,
    ):
        super().__init__(name, path, data_type, label=label)
        self.default = self.data_type(default)
        self.step = self.data_type(step)
        self.range = tuple(self.data_type(i) for i in range_)
        self.field = field

    @classmethod
    def validate(cls, node: PreferenceNode):
        super(Slider, cls).validate(node)
        if not hasattr(node, "range"):
            raise ValueError(f"Slider '{node.name}' must have a range attribute.")
        if not hasattr(node, "field"):
            node.add_property("field", "none")

    @classmethod
    def from_preference_node(cls, node: PreferenceNode):
        super(Slider, cls).from_preference_node(node)
        range_ = cast(tuple[str, str], tuple([i for i in node.range.split(" ")]))
        return cls(
            node.name,
            node.get_path(),
            node.type,
            cast(str, node.default),
            node.step,
            range_,
            node.field,
            label=node.label,
        )


def as_bool(value: DataTypes) -> bool:
    """Convert a string to a boolean."""
    if not isinstance(value, str):
        return bool(value)
    return value.lower() in ("true", "1")


def from_preference_node(node: PreferenceNode) -> Component:
    """Factory function to create a component from a preference node."""
    if node.node_type == "Settings":
        return Settings.from_preference_node(node)
    elif node.node_type == "Field":
        return Field.from_preference_node(node)
    elif node.node_type == "CheckBox":
        return State.from_preference_node(node)
    elif node.node_type == "ColorPicker":
        return Color.from_preference_node(node)
    elif node.node_type == "ComboBox":
        return Combo.from_preference_node(node)
    elif node.node_type == "RadioButton":
        return Radio.from_preference_node(node)
    elif node.node_type == "Slider":
        return Slider.from_preference_node(node)

    raise NotImplementedError(f"Component type {node.node_type} is not supported.")
