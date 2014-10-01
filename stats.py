"""Simulation statistics storage."""

from singleton import Singleton


class Stats(dict, metaclass=Singleton):
    """This is just a singleton dict with some helpers."""
