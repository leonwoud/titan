import os

from titan.resources import get_resources_directory


class QmlComponentNotFoundError(Exception):
    """An exception raised when a component is not found."""


def get_component(component_name: str) -> str:
    """Get the file path to the given component.

    Args:
        component_name (str): The name of the component to retrieve.

    Returns:
        str: The file path to the given component.

    Raises:
        ValueError: If the component is not found in the directory.
    """
    component_dir = os.path.join(get_resources_directory(), "qml", "components")
    components = {os.path.splitext(c)[0]: c for c in os.listdir(component_dir)}
    if component_name not in components:
        raise QmlComponentNotFoundError(
            f"Component {component_name} not found in {component_dir}"
        )

    return os.path.join(component_dir, components[component_name])
