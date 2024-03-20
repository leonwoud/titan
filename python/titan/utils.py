from __future__ import annotations

from typing import Callable


class _MetaDummyClass(type):
    """A metaclass that allows DummyClass to be used as a stand-in for any
    class that is not available in the current environment."""

    def __getattr__(cls, name: str) -> Callable[..., DummyClass]:
        return DummyClass


class DummyClass(metaclass=_MetaDummyClass):
    """A dummy class that can be used to replace any class that is not
    available in the current environment.
    """

    def __init__(*args, **kwargs) -> None:
        pass

    def __call__(self, *args, **kwargs) -> DummyClass:
        return self


def dummy_function(*args, **kwargs):
    """A dummy function that can be used to replace any function that is not
    available in the current environment.
    """
    pass


def dummy_decorator(fn: Callable) -> Callable:
    """A dummy decorator that can be used to replace any decorator that is not
    available in the current environment."""

    def wrapper(*args, **kwargs) -> Callable:
        return fn(*args, **kwargs)

    return wrapper
