"""Simulation statistics storage."""

from activity_distribution import HOUR
from activity_distribution import WEEK
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

    def add_to_bin(self, key, value, env):
        """Add a value to statistic binned by time."""
        hour = (env.now % WEEK(1)) // HOUR(1)
        self.setdefault(key, {}).setdefault(hour, []).append(value)

    def __getitem__(self, key):
        try:
            return super(Stats, self).__getitem__(key)
        except:
            return 0
