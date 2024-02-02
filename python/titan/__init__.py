import os

def qml_resource_dir():
    """Return the directory containing the QML resources."""
    return os.path.join(os.path.dirname(__file__), "qml")