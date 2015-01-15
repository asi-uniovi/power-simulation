"""Simulation statistics storage."""

from singleton import Singleton


class Stats(dict):
    """This is just a singleton dict with some helpers."""

    __metaclass__ = Singleton

    def increment(self, key, inc=1):
        """Increments by inc a key. Creates the key if not existing."""
        self[key] = self.get(key, 0) + inc

    def __getitem__(self, key):
        try:
            return super(Stats, self).__getitem__(key)
        except:
            return 0
