from __future__ import annotations
from typing import Optional, Union
from titan.qt import QtCore

from .components import Group, Component, from_preference_node
from .parser import PreferenceNode, load_preferences_from_file


class AmbiguousPreferenceError(Exception):
    """Raised when asked for a component by name and multiple components are found."""


class Preferences(QtCore.QSettings):
    """Preferences class that extends QSettings to provide additional functionality."""

    preference_updated = QtCore.Signal(str, object)

    def __init__(
        self,
        name: str,
        scope: QtCore.QSettings.Scope,
        application: str,
        organization: str,
    ):
        super().__init__(scope, organization, application)
        self.name = name
        self.scope = scope
        self.application = application
        self.organization = organization
        self._components = {}

    @classmethod
    def from_file(cls, file_path: str) -> Preferences:
        """Create preferences from a file."""
        preference_tree = load_preferences_from_file(file_path)
        components = get_components(preference_tree)
        settings = components[0]
        inst = cls(
            settings.name,
            settings.scope,
            settings.application,
            settings.organization,
        )
        for component in components[1:]:
            component.set_preferences(inst)
            inst._add_component(component)
        return inst

    def _add_component(self, component: Component) -> None:
        """Add a component to the preferences.

        If the component path is a single name, it will be added to the root of the preferences.
        Otherwise, the path will be turned into a group structure so that the component can be
        accessed by attributes. For example, a component with a path of /group1/group2/component
        can be accessed as self.group1.group2.component.
        """
        path = component.path.split("/")

        # Add the component to the root of the preferences
        if len(path) == 1:
            setattr(self, component.name, component)

        # Create attribute accessible path to the component
        else:
            # Create the first group if it does not exist
            if not hasattr(self, path[0]):
                setattr(self, path[0], Group(path[0]))
            grp = getattr(self, path[0])
            for name in path[1:-1]:
                grp = getattr(grp, name)
            grp.add_component(component)

        # Store the components by path, to allow for non-unique names
        self._components[component.path] = component

    def find(self, name: str) -> Optional[Component]:
        """Returns a component by name.

        Useful if you know the name of the preference you want access too,
        without having to know the path to it.

        Raises:
            AmbiguousPreferenceError: If multiple components are found with the same name.
        """
        components = [c for c in self._components.values() if c.name == name]
        if len(components) > 1:
            paths = [c.path for c in components]
            raise AmbiguousPreferenceError(
                f"Multiple components found with name {name}.\n{paths}"
            )
        return components[0] if components else None

    def list_preferences(self) -> None:
        """List the preference paths."""
        for path in sorted(self._components.keys()):
            print(path)

    def set_value(self, path: str, value: Union[str, int, float]) -> None:
        """Set a value in the preferences."""
        self.setValue(path, value)
        self.preference_updated.emit(path, value)

    def get_value(self, path: str) -> Optional[Union[str, int, float]]:
        """Get a value from the preferences."""
        return self.value(path)


def get_components(preference_node: PreferenceNode) -> list[Component]:
    """Returns the preference components."""
    components = []
    for child in preference_node.children:
        if child.children:
            # Check if the children are only of type 'Item' if so, we
            # stop the search here
            if all(child.node_type == "Item" for child in child.children):
                components.append(from_preference_node(child))
            else:
                components.extend(get_components(child))
        else:
            components.append(from_preference_node(child))
    return components
