"""Simulation stats container."""

import injector
import numpy

from activity_distribution import ActivityDistribution
from base import Base
from histogram import Histogram
from module import Binder, CustomInjector


@injector.singleton
@injector.inject(_activity_distribution=ActivityDistribution)
class Stats(Base):
    """This is just a singleton dict with some helpers."""

    def __init__(self):
        super(Stats, self).__init__()
        self.__storage = {}
        self.__builder = CustomInjector(Binder()).get(
            injector.AssistedBuilder(cls=Histogram))

    @property
    def _idle_timeout(self):
        """Indicates the global idle timeout."""
        return self._activity_distribution.global_idle_timeout()

    def user_satisfaction(self):
        """Calculates de user satisfaction."""
        return (
            self.get_count_lower_than('INACTIVITY_TIME', self._idle_timeout)
            / self.count_histogram('INACTIVITY_TIME') * 100)

    def removed_inactivity(self):
        """Calculates how much inactive has been removed."""
        return (sum(i - self._idle_timeout
                    for i in self.get_all_histogram('INACTIVITY_TIME')
                    if i > self._idle_timeout)
                / self.sum_histogram('INACTIVITY_TIME') * 100)

    def append(self, key, value, timestamp=None):
        """Inserts a new value for a key at now.."""
        if key not in self.__storage:
            self.__storage[key] = self.__builder.build(name=key)
        if timestamp is None:
            timestamp = self._env.now
        self.__storage[key].append(timestamp, value)

    def get_all_hourly_histograms(self, key):
        """Gets all the subhistograms per hour."""
        return self.__storage[key].get_all_hourly_histograms()

    def get_all_hourly_summaries(self, key, summaries=('mean', 'median')):
        """Gets all the summaries per hour."""
        return self.__storage[key].get_all_hourly_summaries(summaries)

    def get_all_histogram(self, key):
        """Gets all of the histogram data."""
        return self.__storage[key].get_all_histogram()

    def get_all_hourly_count(self, key):
        """Gets all the count per hour."""
        return self.__storage[key].get_all_hourly_count()

    def sum_histogram(self, key):
        """Sums one histogram elements."""
        try:
            return self.__storage[key].sum_histogram()
        except KeyError:
            return 0.0

    def count_histogram(self, key):
        """Counts one histogram elements."""
        try:
            return self.__storage[key].count_histogram()
        except KeyError:
            return 0

    def get_count_lower_than(self, key, x):
        """Counts the number of elements with value lower than x."""
        try:
            return self.__storage[key].get_count_lower_than(x)
        except KeyError:
            return 0
