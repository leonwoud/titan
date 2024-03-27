from __future__ import annotations

from typing import TYPE_CHECKING, Optional, TypeVar

from titan.qt import QtCore
from .parser import PreferenceNode

if TYPE_CHECKING:
    from .main import Preferences

Number = TypeVar("Number", int, float)
DataTypes = TypeVar("DataTypes", str, float, int)


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

    def __getattr__(self, name: str) -> Group:
        obj = Group(name)
        self.__dict__[name] = obj
        return obj

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


class Component:

    DataTypes = {
        "int": int,
        "str": str,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
    }

    def __init__(self, name: str, path: str, label: Optional[str] = None):
        self.name = name
        self.path = path
        self.label = label
        self.preferences: Preferences = None

    @classmethod
    def validate(self, node: PreferenceNode) -> bool:
        """Validate the preference node contains the required attributes for this
        component and/or create the missing attributes if applicable."""
        # Label is optional, if it does not exist, we will default to None
        if not hasattr(node, "label"):
            node.add_property("label", None)

        if not hasattr(node, "name"):
            raise ValueError(
                f"{node.node_type} ({node.name}) node must have a name attribute."
            )
        if not hasattr(node, "default"):
            raise ValueError(
                f"{node.node_type} ({node.name}) must have a default attribute."
            )

    @classmethod
    def from_preference_node(cls, node: PreferenceNode) -> Component:
        """Create a component from a preference node."""
        cls.validate(node)

    def set_preferences(self, preferences: Preferences) -> None:
        """Set the preferences object for this component."""
        self.preferences = preferences

    def get_value(self) -> DataTypes:
        """Get the value from the preferences."""
        value = self.preferences.get_value(self.path)
        if value is None:
            value = self.default
        if hasattr(self, "data_type"):
            return self.data_type(value)
        return value


class Settings(Component):

    def __init__(self, name, scope, application, organization):
        super().__init__(name, None, None)
        self.scope = self._get_scope(scope)
        self.application = application
        self.organization = organization

    @staticmethod
    def _get_scope(scope: str) -> QtCore.QSettings.Scope:
        """Get the QSettings scope from a string."""
        _scope = QtCore
        for attr in scope.split(".")[1:]:
            _scope = getattr(_scope, attr)
        return _scope

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
    def from_preference_node(cls, node: PreferenceNode):
        # default and name properties aren't needed for the Settings component
        # If they're not given, it shouldn't fail.
        if not hasattr(node, "default"):
            node.add_property("default", None)
        if not hasattr(node, "name"):
            node.add_property("name", None)
        super(Settings, cls).from_preference_node(node)
        return cls(node.name, node.scope, node.application, node.organization)


class Field(Component):

    def __init__(
        self,
        name: str,
        path: str,
        data_type: str,
        default: str,
        range_: Optional[tuple] = None,
        label: Optional[str] = None,
    ):
        super().__init__(name, path, label=label)
        self.data_type = self.DataTypes.get(data_type)
        self.default = self.data_type(default)
        self.range = tuple(self.data_type(i) for i in range_) if range_ else None

    @classmethod
    def validate(cls, node: PreferenceNode):
        super(Field, cls).validate(node)
        if not hasattr(node, "type"):
            raise ValueError(f"Field '{node.name}' must have a type attribute.")

        # Validate we can convert the default value to the specified data type
        data_type = cls.DataTypes.get(node.type)
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
        return cls(node.name, node.get_path(), node.type, node.default, range_=range_)


class CheckBox(Component):

    def __init__(self, name: str, path: str, default: str, label: Optional[str] = None):
        super().__init__(name, path, label=label)
        self.default = as_bool(default)

    @classmethod
    def validate(cls, node: PreferenceNode):
        super(CheckBox, cls).validate(node)

    @classmethod
    def from_preference_node(cls, node: PreferenceNode):
        super(CheckBox, cls).validate(node)
        return cls(node.name, node.get_path(), node.default)


class ColorPicker(Component):

    def __init__(self, name: str, path: str, default: str, label: Optional[str] = None):
        super().__init__(name, path, label=label)
        self.default = default

    @classmethod
    def from_preference_node(cls, node: PreferenceNode):
        super(ColorPicker, cls).from_preference_node(node)
        return cls(node.name, node.get_path(), node.default)


class TypedItemComponent(Component):
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
        super().__init__(name, path, label=label)
        self.data_type = self.DataTypes.get(data_type)
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
        data_type = cls.DataTypes.get(node.type)
        try:
            data_type(node.default)
        except ValueError:
            raise ValueError(f"Invalid default value for {cls.__name__} '{node.name}'")

    @classmethod
    def from_preference_node(cls, node: PreferenceNode):
        super(TypedItemComponent, cls).from_preference_node(node)
        items = [child.name for child in node.children]
        return cls(
            node.name, node.get_path(), node.type, items, node.default, label=node.label
        )


class ComboBox(TypedItemComponent):
    """A combo box component."""

    pass


class RadioButton(TypedItemComponent):
    """A radio button component."""

    pass


def as_bool(value: str) -> bool:
    """Convert a string to a boolean."""
    if value.lower() in ("true", "1"):
        return True
    return False


def from_preference_node(node: PreferenceNode) -> Component:
    """Factory function to create a component from a preference node."""
    if node.node_type == "Settings":
        return Settings.from_preference_node(node)
    elif node.node_type == "Field":
        return Field.from_preference_node(node)
    elif node.node_type == "CheckBox":
        return CheckBox.from_preference_node(node)
    elif node.node_type == "ColorPicker":
        return ColorPicker.from_preference_node(node)
    elif node.node_type == "ComboBox":
        return ComboBox.from_preference_node(node)
    elif node.node_type == "RadioButton":
        return RadioButton.from_preference_node(node)

    raise NotImplementedError(f"Component type {node.node_type} is not supported.")
