from __future__ import annotations
import re
from typing import Any, Optional

# Multi-line strings need to be wrapped in three double-quotes
# Use html tags for newlines in tooltips, not line break characters


class PreferenceNode:
    """A class that represents a node in a preference file."""

    Type = re.compile("^\s*\[(.*?)\]")
    Property = re.compile('^\s*- ([a-zA-Z]+) (?:")?(.*?)(?:")?$')

    def __init__(self, node_type: str) -> None:
        self._node_type: str = node_type
        self._parent: PreferenceNode = None
        self._children: list[PreferenceNode] = []
        self._properties: dict[str, str] = {}
        self._index = -1
        self._name = None

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
            path.append(node.name)
            node = node.parent
        return "/".join(reversed(path))

    def recursive_print(self, indent: int = 0) -> None:
        """Recursively print the node and its children."""
        print(" " * indent + f"{self.node_type} {self.get_path()}")
        for child in self.children:
            child.recursive_print(indent + 4)


def preprocess_preference_file(preference_file: str) -> list[str]:
    """Reads a preference file from disk, removes comments, converts multi-line
    strings into single line strings and converts space indentations into tabs.

    Args:
        preference_file: The path to the preference file.

    Returns:
        The contents of the file with comments removed, multi-line strings converted
        to single line strings and space indentations converted to tabs.
    """

    # This may not be the most efficient way to do this, but it is simple and
    # easy enough to understand. The files we're pre-processing are not large
    # so the performance hit should be minimal at best.

    def get_n_vals(n: int, it: iter) -> list:
        """Get the next n values from an iterator. If the iterator is exhausted,
        None will be returned in place of the missing values."""
        return [next(it, None) for _ in range(n)]

    contents = None
    with open(preference_file, "r") as handle:
        contents = handle.read()

    # Replace tab characters with 4 spaces to begin with, this just
    # ensures we have a consistent starting point.
    contents = contents.replace("\t", "    ")

    is_comment = False
    multi_line_string = False
    multi_line_comment = False

    processed = []
    iter_contents = iter(contents)
    for chr in iter_contents:

        # First, check of this is a multi-line comment as everything
        # else gets ignored until the comment ends
        if chr == "/":
            next_val = get_n_vals(1, iter_contents)[0]
            if next_val == "*":
                multi_line_comment = True
                continue
            else:
                processed.append(next_val)
                continue

        # If we're in a multi-line comment, check if this is the end
        if chr == "*":
            if multi_line_comment:
                next_val = get_n_vals(1, iter_contents)[0]
                if next_val == "/":
                    multi_line_comment = False
                continue

        # Dont append anything, we're inside a multi-line comment
        if multi_line_comment:
            continue

        # Check if this is the start of a comment, if so
        # we ignore all proceeding chrs until the next line break
        if chr == "#":
            is_comment = True

        if is_comment:
            if chr == "\n":
                is_comment = False
            else:
                continue

        if chr == '"':
            # Check if this is a multi-line string by looking ahead
            next_vals = [v for v in get_n_vals(2, iter_contents) if v]
            if next_vals == ['"', '"']:
                multi_line_string = not multi_line_string
                processed.append('"')
                continue

            # If we're in a multi-line string, we need to escape
            # any double quotes.
            quote_chr = ['\\"'] if multi_line_string else ['"']
            processed.extend(quote_chr + next_vals)
            continue

        # Check if this is a newline inside of a multi-line string
        if chr == "\n" and multi_line_string:
            # Keep reading until we reach a non space chr
            next_chr = next(iter_contents, None)
            while next_chr and next_chr == " ":
                next_chr = next(iter_contents, None)
                continue
            processed.append(next_chr)
            continue

        # Finally we just add what ever chr we're at in the file
        processed.append(chr)

    # Merge the processed list into a single string
    processed = "".join(processed)

    # This regular expression is used to detect how many spaces were used
    # for indentation.
    regex = re.compile(r"^ [^-]*")

    # Split the processed string into lines and convert indents to tabs
    # this makes it easier to parse the file into nodes.
    lines = []
    num_spaces = 0
    for line in processed.split("\n"):
        if num_spaces == 0:
            indented = regex.match(line)
            if indented:
                # Encountered the first indented line
                num_spaces = len(indented.group(0))
            if num_spaces == 1:
                raise RuntimeError("Malformed file, tabs should be at least 2 spaces")
        if num_spaces > 1:
            line = line.replace(" " * num_spaces, "\t")
        if line:
            lines.append(line)

    return lines


def indents(line: str) -> int:
    """Returns the number of indentations in a line."""
    return line.count("\t")


def create_preference_tree(contents: list[str]) -> PreferenceNode:
    """Builds a tree of nodes from the contents of a preference file.

    Args:
        contents: The contents of the preference file.

    Returns:
        A list of nodes that represent the structure of the preference file.
    """

    def get_parent(nodes: list[PreferenceNode], index: int) -> Optional[PreferenceNode]:
        """Returns the parent node of the current node."""
        for node in reversed(nodes):
            if node.index == index:
                return node

    def get_node_type(line: str) -> Optional[str]:
        """Returns the node type of a line."""
        match = PreferenceNode.Type.match(line)
        if match:
            return match.group(1)

    def get_property(line: str) -> Optional[tuple[str, str]]:
        """Returns the property of a line."""
        match = PreferenceNode.Property.match(line)
        if match:
            return match.groups()

    root = PreferenceNode("root")
    root.index = -1
    root.name = "root"
    nodes = [root]

    for line in contents:
        indent = indents(line)
        node_type = get_node_type(line)

        if node_type:
            node = PreferenceNode(node_type)
            node.index = indent
            parent = get_parent(nodes, indent - 1)
            parent.add_child(node)
            nodes.append(node)
            continue

        prop = get_property(line)
        if prop:
            node.add_property(*prop)

    return root


def load_preferences_from_file(file_path: str) -> PreferenceNode:
    """Load preferences from a file."""
    contents = preprocess_preference_file(file_path)
    return create_preference_tree(contents)
