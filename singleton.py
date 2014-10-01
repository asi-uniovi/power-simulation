"""Enables singleton classess via a metaclass."""


class Singleton(type):
    """Singleton metaclass.

    Stores the instance on the class itself and overrides the construction via
    __call__() on the type.
    """

    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)
        cls.__instance = None

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = type.__call__(cls, *args, **kwargs)
        return cls.__instance
