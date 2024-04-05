from __future__ import annotations

from typing import Any, Optional, TypeVar, Union

from titan.qt import QtCore, QtWidgets
from titan.widgets import CollapsibleContainer

from titan._internal.preferences.components import (
    Group,
    Component,
    as_bool,
    from_preference_node,
)
from titan._internal.preferences.parser import (
    PreferenceNode,
    load_preferences_from_file,
)
from titan._internal.preferences.widgets import (
    CheckBox,
    ColorPicker,
    ComboBox,
    Field,
    RadioButtons,
    Slider,
)

# TypeVar for the return type of from_component
PreferenceWidget = TypeVar(
    "PreferenceWidget", CheckBox, ColorPicker, ComboBox, Field, RadioButtons, Slider
)


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
        self._file_path = None

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
        inst._file_path = file_path
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

    def get_component(self, path: str) -> Optional[Component]:
        """Returns a component by path."""
        return self._components.get(path)

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

    def list_paths(self) -> None:
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

    @property
    def file_path(self) -> str:
        """The file path of the preferences."""
        return self._file_path


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


def from_component(component: Component) -> PreferenceWidget:
    """Return the appropriate widget for the given component.

    Args:
        component (Component): The component to create a widget for.

    Returns:
        The created preference widget.
    """

    if component.type == component.Type.State:
        return CheckBox.from_component(component)
    elif component.type == component.Type.Color:
        return ColorPicker.from_component(component)
    elif component.type == component.Type.Combo:
        return ComboBox.from_component(component)
    elif component.type == component.Type.Field:
        return Field.from_component(component)
    elif component.type == component.Type.Radio:
        return RadioButtons.from_component(component)
    elif component.type == component.Type.Slider:
        return Slider.from_component(component)

    raise ValueError(f"Invalid component: {component}")


class Label(QtWidgets.QLabel):
    def __init__(
        self, text: str, default: Any, parent: Optional[QtWidgets.QWidget] = None
    ):
        super().__init__(text, parent=parent)
        self.setFixedWidth(100)
        self._default = default
        self.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    @QtCore.Slot(object)
    def on_value_changed(self, value: Any) -> None:
        self.update_font(value)

    def update_font(self, value: Any) -> None:
        font = self.font()
        is_default = value == self._default
        font.setBold(not is_default)
        font.setItalic(not is_default)
        self.setFont(font)


class PreferenceFormLayout(QtWidgets.QFormLayout):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent=parent)

    def add_row(self, label: str, widget: PreferenceWidget) -> None:
        label = Label(label, widget.default)
        label.update_font(widget.get_value())
        super().addRow(label, widget)
        widget.value_changed.connect(label.on_value_changed)

    def add_widget(self, widget: QtWidgets.QWidget) -> None:
        super().addRow(widget)


class PreferenceGroup(QtWidgets.QWidget):

    def __init__(
        self,
        title: str,
        is_collapsible: bool,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._container = CollapsibleContainer(
            title=title, is_collapsible=is_collapsible, parent=self
        )
        self._form_layout = PreferenceFormLayout(self._container.contents)
        layout.addWidget(self._container)

    def add_component(self, component: Component) -> None:
        """Add a component to the group.

        Args:
            component: The component to add.
        """
        widget = from_component(component)
        label = "" if component.type == component.Type.State else component.label
        self._form_layout.add_row(label, widget)

    def add_widget(self, widget: QtWidgets.QWidget) -> None:
        """Add a widget to the group.

        Args:
            widget: The widget to add.
        """
        self._form_layout.add_widget(widget)


class Tabs(QtWidgets.QTabWidget):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent=parent)

    def add_tab(self, node: PreferenceNode, preferences: Preferences) -> None:
        # self.addTab(widget, title)
        widget = create_preferences_widget(preferences, node)
        self.addTab(widget, node.label)


def create_tabs(node: PreferenceNode, preferences: Preferences) -> Tabs:
    """Create a tab widget from a preference node.

    Recursively creates tabs and components from the preference node.

    Args:
        node: The preference node to create the tabs from.
        preferences: The preferences object to get the components from.

    Returns:
        The created tab widget.
    """
    tabs = Tabs()
    for child in node.children:
        if child.node_type == "Tab":
            tabs.add_tab(child, preferences)
        else:
            raise ValueError(f"Invalid node type: {child.node_type}")
    return tabs


def create_group(node: PreferenceNode, preferences: Preferences) -> PreferenceGroup:
    """Create a group widget from a preference node.

    Recursively creates groups and components from the preference node.

    Args:
        node: The preference node to create the group from.
        preferences: The preferences object to get the components from.

    Returns:
        The created group widget.
    """
    collapsible = as_bool(
        node.collapsible if node.has_property("collapsible") else "false"
    )
    grp = PreferenceGroup(node.label, collapsible)
    for child in node.children:
        if child.node_type == "Group":
            child_grp = create_group(child, preferences)
            grp.add_widget(child_grp)
        elif child.node_type == "Tabs":
            tabs = create_tabs(child, preferences)
            grp.add_widget(tabs)
        else:
            component = preferences.get_component(child.get_path())
            grp.add_component(component)
    return grp


def create_preferences_widget(
    preferences: Preferences, preference_node: Optional[PreferenceNode] = None
) -> QtWidgets.QWidget:
    """Create a preferences widget from a preference structure.

    Args:
        preferences: The preferences object to get the components from.
        preference_node: The preference node to create the preferences from, if None given
            preferences will be loaded from the preferences file contained in the preferences object.

    Returns:
        The created preferences widget.
    """
    widget = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(widget)
    form_layout = PreferenceFormLayout()
    layout.addLayout(form_layout)

    if preference_node is None:
        preference_node = load_preferences_from_file(preferences.file_path)

    for child in preference_node.children:
        if child.node_type == "Settings":
            continue
        elif child.node_type == "Group":
            group = create_group(child, preferences)
            form_layout.add_widget(group)
        elif child.node_type == "Tabs":
            tabs = create_tabs(child, preferences)
            form_layout.add_widget(tabs)
        else:
            child_comp = preferences.get_component(child.get_path())
            child_widget = from_component(child_comp)
            # We make the label a blank string for State components, as the label is
            # already displayed on the checkbox itself.
            label = "" if child_comp.type == child_comp.Type.State else child_comp.label
            form_layout.add_row(label, child_widget)

    layout.addStretch()
    return widget
