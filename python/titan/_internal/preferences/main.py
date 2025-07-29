from __future__ import annotations

from typing import Any, Optional, Union, cast, TYPE_CHECKING, Protocol

from titan.qt import QtCore, QtGui, QtWidgets
from titan.widgets import CollapsibleContainer


from titan._internal.preferences.components import (
    Component,
    Group,
    Settings,
    as_bool,
    from_preference_node,
)

if TYPE_CHECKING:
    # Protocol for widgets that can be used in PreferenceLabel
    class PreferenceWidgetProtocol(Protocol):
        def get_value(self) -> Any: ...
        def set_value(self, value: Any, read_only: bool = False) -> None: ...
        @property
        def default(self) -> Any: ...
        # value_changed: QtCore.Signal  TODO: Doesn't work, not sure why


from titan._internal.preferences.parser import (
    PreferenceNode,
    load_preferences_from_file,
)
from titan._internal.preferences.widgets import (
    CheckBox,
    ColorPicker,
    ComboBox,
    Field,
    PreferenceBase,
    RadioButtons,
    Slider,
)


PreferenceComponent = Union[
    CheckBox, ColorPicker, ComboBox, Field, RadioButtons, Slider
]


class AmbiguousPreferenceError(Exception):
    """Raised when asked for a component by name and multiple components are found."""


class Preferences(QtCore.QSettings):
    """Preferences class that extends QSettings to provide additional functionality."""

    preference_updated = QtCore.Signal(str, object)

    def __getattr__(self, name: str) -> Component:
        """Provide typing support for dynamically added components."""
        # This is only called when the attribute doesn't exist normally
        # The actual attributes are set by _add_component()
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def __init__(
        self,
        name: str,
        scope: QtCore.QSettings.Scope,
        application: str,
        organization: str,
    ):
        super().__init__(scope, organization, application)
        self.name = name
        self._components = {}
        self._file_path: str

    @classmethod
    def from_file(
        cls, file_path: str, application: Optional[str] = None
    ) -> Preferences:
        """Create preferences from a JSON file.

        Args:
            file_path: The path to the JSON preferences file.
            application: The application name to use for the preferences. This
                is useful if the same base preferences are used by multiple applications.
        """
        preference_tree = load_preferences_from_file(file_path)
        components = get_components(preference_tree)
        settings = cast(Settings, components[0])
        inst = cls(
            settings.name,
            settings.scope,
            application or settings.application,
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
        """Set a value in the preferences.

        Args:
            path: The path to the preference.
            value: The value to set.
        """
        self.setValue(path, value)

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
        # Special handling for Settings component - always include it first
        if child.node_type == "Settings":
            components.insert(0, from_preference_node(child))
            # Then process its children
            components.extend(get_components(child))
        elif child.children:
            # Check if the children are only of type 'Item' if so, we
            # stop the search here
            if all(child.node_type == "Item" for child in child.children):
                components.append(from_preference_node(child))
            else:
                components.extend(get_components(child))
        else:
            components.append(from_preference_node(child))
    return components


def from_component(component: Component) -> PreferenceComponent:
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


class PreferenceLabel(QtWidgets.QPushButton):
    def __init__(
        self,
        label_text: str,
        widget: PreferenceWidgetProtocol,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        self._label = QtWidgets.QLabel(label_text)
        self._label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.setFixedSize(100, 20)
        self.setFlat(True)
        self._widget = widget
        self._current_value: Optional[Any] = None
        self.clicked.connect(self._on_clicked)

    @QtCore.Slot(object)
    def on_value_changed(self, value: Any) -> None:
        self.update_font(value)

    @QtCore.Slot()
    def _on_clicked(self) -> None:
        value = self._widget.get_value()
        if value != self._widget.default and self._widget.default is not None:
            self._widget.set_value(self._widget.default)
            self.update_font(self._widget.default)
            self._current_value = value
        elif self._current_value is not None:
            self._widget.set_value(self._current_value)
            self.update_font(self._current_value)

    def update_font(self, value: Any) -> None:
        font = self.font()
        is_default = value == self._widget.default
        font.setBold(not is_default)
        font.setItalic(not is_default)
        self.setFont(font)


class PreferenceFormLayout(QtWidgets.QFormLayout):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent=parent)

    def add_row(self, label: str, widget: PreferenceWidgetProtocol) -> None:
        label_widget = PreferenceLabel(label, widget)
        label_widget.update_font(widget.get_value())
        cast(Any, widget).value_changed.connect(label_widget.on_value_changed)
        super().addRow(label, cast(QtWidgets.QWidget, widget))

    def add_widget(self, widget: QtWidgets.QWidget) -> None:
        super().addRow(widget)


class PreferenceGroup(QtWidgets.QWidget):

    refresh_requested = QtCore.Signal()

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
        label = "" if component.type == component.Type.State else component.label or ""
        cast(Any, widget).value_changed.connect(self.refresh_requested)
        self.add_row(label, widget)

    def add_row(self, label: str, widget: PreferenceWidgetProtocol) -> None:
        """Add a row to the group.

        Args:
            label: The label for the widget.
            widget: The widget to add.
        """
        cast(Any, widget).value_changed.connect(self.refresh_requested)
        self._form_layout.add_row(label, widget)

    def add_widget(
        self, widget: Union[PreferenceWidget, PreferenceGroup, Tabs]
    ) -> None:
        """Add a widget to the group.

        Args:
            widget: The widget to add.
        """
        widget.refresh_requested.connect(self.refresh_requested)
        self._form_layout.add_widget(widget)


class Tabs(QtWidgets.QTabWidget):

    refresh_requested = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent=parent)

    def add_tab(self, node: PreferenceNode, preferences: Preferences) -> None:
        widget = create_preferences_widget(preferences, node)
        widget.refresh_requested.connect(self.refresh_requested)
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
        if child.has_property("visible") and not as_bool(child.visible):
            continue

        if child.node_type == "Group":
            child_grp = create_group(child, preferences)
            grp.add_widget(child_grp)

        elif child.node_type == "Compound":
            compound = Compound.from_preference_node(child, preferences)
            grp.add_row(child.label, compound)

        elif child.node_type == "Tabs":
            tabs = create_tabs(child, preferences)
            grp.add_widget(tabs)

        else:
            component = preferences.get_component(child.get_path())
            if component:
                grp.add_component(component)

    return grp


class PreferenceWidget(QtWidgets.QWidget):

    refresh_requested = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent=parent)


def create_preferences_widget(
    preferences: Preferences, preference_node: Optional[PreferenceNode] = None
) -> PreferenceWidget:
    """Create a preferences widget from a preference structure.

    Args:
        preferences: The preferences object to get the components from.
        preference_node: The preference node to create the preferences from, if None given
            preferences will be loaded from the preferences file contained in the preferences object.

    Returns:
        PreferenceWidget: The created preferences widget.
    """
    widget = PreferenceWidget()
    layout = QtWidgets.QVBoxLayout(widget)
    form_layout = PreferenceFormLayout()
    layout.addLayout(form_layout)

    if preference_node is None:
        preference_node = load_preferences_from_file(preferences.file_path)

    for child in preference_node.children:
        if child.has_property("visible") and not as_bool(child.visible):
            continue

        if child.node_type == "Settings":
            continue

        elif child.node_type == "Group":
            group = create_group(child, preferences)
            group.refresh_requested.connect(widget.refresh_requested)
            form_layout.add_widget(group)

        elif child.node_type == "Compound":
            compound = Compound.from_preference_node(child, preferences)
            compound.value_changed.connect(widget.refresh_requested)
            form_layout.add_row(child.label, compound)

        elif child.node_type == "Tabs":
            tabs = create_tabs(child, preferences)
            tabs.refresh_requested.connect(widget.refresh_requested)
            form_layout.add_widget(tabs)

        else:
            child_comp = preferences.get_component(child.get_path())
            if child_comp:
                child_widget = from_component(child_comp)
                # We make the label a blank string for State components, as the label is
                # already displayed on the checkbox itself.
                label = "" if child_comp.type == child_comp.Type.State else child_comp.label or ""
                child_widget.value_changed.connect(widget.refresh_requested)
                form_layout.add_row(label, child_widget)

    layout.addStretch()
    return widget


class Compound(QtWidgets.QWidget):
    """A Compound widget is a container of other preference widgets."""

    value_changed = QtCore.Signal(object)

    @classmethod
    def from_preference_node(
        cls, preference_node: PreferenceNode, preferences: Preferences
    ) -> Compound:
        inst = cls()
        for child in preference_node.children:
            child_component = from_preference_node(child)
            child_component.set_preferences(preferences)
            child_widget = from_component(child_component)
            inst.add_widget(child_widget)
        return inst

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent=parent)
        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._widgets = []

    def add_widget(self, widget: PreferenceComponent):
        self._widgets.append(widget)
        widget.value_changed.connect(self._on_value_changed)
        self._layout.addWidget(cast(QtWidgets.QWidget, widget))

    @QtCore.Slot()
    def _on_value_changed(self):
        self.value_changed.emit(self.get_value())

    def get_value(self):
        return tuple(widget.get_value() for widget in self._widgets)

    def set_value(self, value, read_only=False):
        for idx, val in enumerate(value):
            self._widgets[idx].set_value(val, read_only)

    def restore_default(self):
        for widget in self._widgets:
            if isinstance(widget, PreferenceBase):
                widget.restore_default()

    def reload(self):
        for widget in self._widgets:
            if isinstance(widget, PreferenceBase):
                widget.reload()

    @property
    def default(self):
        return tuple(widget.default for widget in self._widgets)


class PreferencesDialog(QtWidgets.QDialog):

    refresh_requested = QtCore.Signal()

    def __init__(
        self,
        preferences: Preferences,
        window_title: Optional[str] = None,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        self._preferences = preferences
        window_title = window_title or "Preferences"
        self.setWindowTitle(window_title)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._preferences_widget = create_preferences_widget(preferences)
        self._preferences_widget.refresh_requested.connect(self.refresh_requested)
        layout.addWidget(self._preferences_widget)
        self._watcher = QtCore.QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self.reload)

    def restore_defaults(self) -> None:
        """Restore all preferences to their default values."""
        for child in self._preferences_widget.findChildren(QtWidgets.QWidget):
            if hasattr(child, 'restore_default') and callable(getattr(child, 'restore_default')):
                cast(Any, child).restore_default()

    @QtCore.Slot()
    def reload(self) -> None:
        """Reload the preferences from the preferences file."""
        for child in self._preferences_widget.findChildren(QtWidgets.QWidget):
            if hasattr(child, 'reload') and callable(getattr(child, 'reload')):
                cast(Any, child).reload()

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self._watcher.addPath(self._preferences.fileName())
        self.reload()
        event.accept()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._watcher.removePath(self._preferences.fileName())
        event.accept()
