from functools import cache
import glob
import os

from typing import Optional


class AmbiguousResourceError(Exception):
    """An exception raised when multiple resources with the same name are found."""


def get_resources_directory() -> str:
    """Get the absolute path to the resources directory.

    Returns:
        The absolute path to the resources directory.
    """
    resources_dir = os.path.join(os.path.dirname(__file__), "..", "..", "resources")
    return os.path.normpath(os.path.abspath(resources_dir))


def get_resource(
    relative_resource_path: str, expects_existence: Optional[bool] = True
) -> str:
    """Get the absolute path to a resource that is found in the resources directory given the relative path.

    Args:
        relative_resource_path: The relative path to the resource.
        expects_existance: If True, an exception will be raised if the resource does not exist.

    Returns:
        The absolute path to the resource.

    Raises:
        FileNotFoundError: If the resource does not exist and expects_existence is True.

    Examples:
        resource_path = get_resource("path/to/resource.txt")
    """
    file_path = os.path.normpath(
        os.path.join(get_resources_directory(), relative_resource_path)
    )
    if expects_existence and not os.path.exists(file_path):
        raise FileNotFoundError(f"The resource '{file_path}' does not exist.")
    return file_path


@cache
def find_resource(file_name: str) -> str:
    """Searches for the given resource in the resources directory.

    If multiple resources with the same name exists, an AmbiguousResourceError will be raised.

    Args:
        file_name: The name of the file to find.

    Returns:
        The absolute path to the given resource.

    Raises:
        AmbiguousResourceError: If multiple resources with the same name are found.
        FileNotFoundError: If the resource does not exist.
    """
    resources_dir = get_resources_directory()
    result = glob.glob(f"{resources_dir}{os.sep}**{os.sep}{file_name}", recursive=True)

    if len(result) > 1:
        raise AmbiguousResourceError(
            f"Multiple resources with the name '{file_name}' were found."
        )

    elif len(result) == 1:
        return os.path.normpath(result[0])

    raise FileNotFoundError(f"The resource '{file_name}' does not exist.")
