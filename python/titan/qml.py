import os

def get_component(component_name: str) -> str:
    """Get the file path to the given component.
    
    Args:
        component_name (str): The name of the component to retrieve.
    
    Returns:
        str: The file path to the given component.
        
    Raises:
        ValueError: If the component is not found in the directory.
    """
    component_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "qml",
            "components"
        )
    )

    components = {os.path.splitext(c)[0]: c for c in os.listdir(component_dir)}
    if component_name not in components:
        raise ValueError(f"Component {component_name} not found in {component_dir}")

    return os.path.join(component_dir, components[component_name])