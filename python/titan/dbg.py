from typing import Any, Dict, Optional


def execfile(
        file_path: str,
        globals: Optional[Dict[str, Any]] = None,
        locals: Optional[Dict[str, Any]] = None
):
    """Execute the given file, replacement for python 2's execfile."""
    if globals is None:
        globals = {}
    globals.update({
        "__file__": file_path,
        "__name__": "__main__",
    })
    with open(file_path, 'rb') as file:
        exec(compile(file.read(), file_path, 'exec'), globals, locals)
