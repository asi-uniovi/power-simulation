"""Simulation stats container."""

import injector
import sqlite3

from histogram import Histogram
from module import Binder, CustomInjector, env_key


@injector.singleton
class Stats(dict):
    """This is just a singleton dict with some helpers."""

    @injector.inject(env=env_key, conn=sqlite3.Connection)
    def __init__(self, env, conn):
        super(Stats, self).__init__()
        self._env = env
        self.__conn = conn
        self.__builder = CustomInjector(Binder()).get(
            injector.AssistedBuilder(cls=Histogram))

    def append(self, key, value):
        """Inserts a new value for a key at now.."""
        if key not in self:
            self[key] = self.__builder.build(name=key)
        self[key].append(self._env.now, value)

    def get_hourly_statistics(self, key):
        """Get the stats for a histogram per hour."""
        return self[key].get_hourly_statistics()

    def get_statistics(self, key):
        """Get the stats for a histogram."""
        return self[key].get_statistics()

    def dump_histogram_to_file(self, key, filename):
        """Dumps a histogram key to a file."""
        self[key].dump_to_file(filename)
