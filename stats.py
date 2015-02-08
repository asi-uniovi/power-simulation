"""Simulation statistics storage."""

from singleton import Singleton


class Stats(dict, metaclass=Singleton):
    """This is just a singleton dict with some helpers."""

    def increment(self, key, inc=1):
        """Increments by inc a key. Creates the key if not existing."""
        self[key] = self.get(key, 0) + inc

    def append(self, key, value):
        """Append a new value to a list statistic. Create if non existing."""
        item = self.get(key, [])
        item.append(value)
        self[key] = item

    def __getitem__(self, key):
        try:
            return super(Stats, self).__getitem__(key)
        except:
            return 0
