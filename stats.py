"""Simulation statistics storage."""

from singleton import Singleton


class Stats(dict, metaclass=Singleton):
    """This is just a singleton dict with some helpers."""

    def increment(self, key, inc=1):
        """Increments by inc a key. Creates the key if not existing."""
        self[key] = self.get(key, 0) + inc

    def __getitem__(self, key):
        try:
            return self[key]
        except:
            return 0
