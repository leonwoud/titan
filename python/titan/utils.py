class _MetaDummyClass(type):
    """A metaclass that allows DummyClass to be used as a stand-in for any
    class that is not available in the current environment."""

    def __getattr__(cls, name):
        return DummyClass


class DummyClass(metaclass=_MetaDummyClass):
    """A dummy class that can be used to replace any class that is not
    available in the current environment.
    """

    def __init__(*args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self


def dummy_function(*args, **kwargs):
    """A dummy function that can be used to replace any function that is not
    available in the current environment.
    """
    pass


def dummy_decorator(fn):
    """A dummy decorator that can be used to replace any decorator that is not
    available in the current environment."""

    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper
