from __future__ import annotations

import json
from typing import Any, Dict, Optional


class PreferenceNode:
    """A class that represents a node in a preference file."""

    def __init__(self, node_type: str) -> None:
        self._node_type: str = node_type
        self._parent: PreferenceNode
        self._children: list[PreferenceNode] = []
        self._properties: dict[str, str] = {}
        self._index = -1
        self._name: str = ""

    def __repr__(self):
        return self._node_type

    def __getattr__(self, name: str) -> str:
        if name in self._properties:
            return self._properties[name]
        raise AttributeError(f"'PreferenceNode' object has no attribute '{name}'")

    def add_property(self, name: str, value: str) -> None:
        """Add a property to the node.

        When added, this can then be accessed as an attribute of the node.

        Args:
            name: The name of the property.
            value: The value of the property.
        """
        if name == "name":
            self.name = value
            return
        self._properties[name] = value

    def has_property(self, name: str) -> bool:
        """Returns True if the property exists."""
        return name in self._properties

    def add_child(self, child_node: PreferenceNode) -> None:
        """Add a child as a child of this node."""
        child_node.parent = self
        self._children.append(child_node)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def children(self) -> list[PreferenceNode]:
        return [child for child in self._children]

    @property
    def node_type(self) -> str:
        return self._node_type

    @property
    def parent(self) -> PreferenceNode:
        return self._parent

    @parent.setter
    def parent(self, node: PreferenceNode) -> None:
        self._parent = node

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, index: int) -> None:
        self._index = index

    def get_path(self) -> str:
        """Returns the path of the node."""
        path = []
        node = self
        while node:
            # Don't include the root node in the path
            if node.index == -1:
                break
            # If the node has a name, add it to the path
            if node.name:
                path.append(node.name)
            node = node.parent
        return "/".join(reversed(path))

    def recursive_print(self, indent: int = 0) -> None:
        """Recursively print the node and its children."""
        print(" " * indent + f"{self.node_type} {self.get_path()}")
        for child in self.children:
            child.recursive_print(indent + 4)


def load_preferences_from_file(file_path: str) -> PreferenceNode:
    """Load preferences from a JSON file.

    Args:
        file_path: Path to the JSON preference file.

    Returns:
        Root PreferenceNode containing the parsed preference tree.
    """
    with open(file_path, "r") as f:
        data = json.load(f)

    return _create_node_tree(data)


def _create_node_tree(
    data: Dict[str, Any], parent: Optional[PreferenceNode] = None
) -> PreferenceNode:
    """Recursively create PreferenceNode tree from JSON data.

    Args:
        data: Dictionary containing node data.
        parent: Parent node (None for root).

    Returns:
        Created PreferenceNode.
    """
    if parent is None:
        # Create root node
        root = PreferenceNode("root")
        root.index = -1
        root.name = "root"

        # Process top-level structure
        if "component_type" in data:
            # Single component at root - create it directly
            if data["component_type"] == "Settings":
                # Settings is special - create it but don't add its children to it
                # Instead, flatten the children to root level for original behavior compatibility
                settings_data = data.copy()
                settings_children = settings_data.pop(
                    "children", []
                )  # Remove children from settings

                settings_node = _create_single_node(
                    settings_data
                )  # Create settings without children
                root.add_child(settings_node)

                # Add Settings children directly to root level
                for child_data in settings_children:
                    child = _create_single_node(child_data)
                    child.index = 0  # Set correct index for top-level children
                    root.add_child(child)
            else:
                child = _create_single_node(data)
                root.add_child(child)
        else:
            # Multiple components or structured data
            for key, value in data.items():
                if key == "children":
                    # Process children array
                    for child_data in value:
                        child = _create_single_node(child_data)
                        root.add_child(child)
                elif isinstance(value, dict) and "component_type" in value:
                    # Named component
                    child = _create_single_node(value)
                    if not child.name:
                        child.name = key
                    root.add_child(child)
                elif isinstance(value, dict):
                    # Treat as component with implicit type from key
                    component_data = value.copy()
                    component_data["component_type"] = key
                    child = _create_single_node(component_data)
                    root.add_child(child)

        return root

    return _create_single_node(data, parent)


def _create_single_node(
    data: Dict[str, Any], parent: Optional[PreferenceNode] = None
) -> PreferenceNode:
    """Create a single PreferenceNode from data.

    Args:
        data: Dictionary containing node data.
        parent: Parent node.

    Returns:
        Created PreferenceNode.
    """
    component_type = data.get("component_type", "Unknown")
    node = PreferenceNode(component_type)

    # Set index based on parent
    if parent:
        node.index = parent.index + 1
    else:
        node.index = 0

    # Process all properties except children and component_type
    for key, value in data.items():
        if key in ("children", "component_type"):
            continue

        # Convert value to string as expected by PreferenceNode
        if isinstance(value, (dict, list)):
            # Skip complex types that aren't simple properties
            continue
        elif value is None:
            node.add_property(key, "null")
        elif isinstance(value, bool):
            node.add_property(key, "true" if value else "false")
        else:
            node.add_property(key, str(value))

    # Process children
    children = data.get("children", [])
    for child_data in children:
        child = _create_single_node(child_data, node)
        node.add_child(child)

    return node
