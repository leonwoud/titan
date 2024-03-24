from __future__ import annotations
from typing import Any
from titan.qt import QtCore

from .components import Component, from_preference_node
from .parser import PreferenceNode, load_preferences_from_file


class Container:

    def __init__(self, name):
        self._name = name

    def __getattr__(self, name):
        obj = Container(name)
        self.__dict__[name] = obj
        return obj


class Preferences(QtCore.QSettings):
    """Preferences class that extends QSettings to provide additional functionality."""

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
            inst._add_component(component)
        return inst

    def _add_component(self, component: Component) -> None:
        """Add a component to the preferences."""
        if component.name in self._components:
            raise ValueError(f"Component with name {component.name} already exists.")
        path = component.path.split("/")
        # Add the component to the root of the preferences
        if len(path) == 1:
            setattr(self, component.name, component)
        # Create a path of containers to the component
        else:
            if not hasattr(self, path[0]):
                setattr(self, path[0], Container(path[0]))
            container = getattr(self, path[0])
            for name in path[1:-1]:
                container = getattr(container, name)
            setattr(container, component.name, component)
        self._components[component.name] = component


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
