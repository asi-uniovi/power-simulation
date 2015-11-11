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

    def get_hourly_histogram(self, key, hour):
        """Gets the subhistogram for one particular hour."""
        return self[key].get_hourly_histogram(hour)

    def get_all_hourly_histograms(self, key):
        """Gets all the subhistograms per hour."""
        return self[key].get_all_hourly_histograms()

    def get_all_hourly_summaries(self, key, summaries=['mean', 'median']):
        """Gets all the summaries per hour."""
        return self[key].get_all_hourly_summaries(summaries)
