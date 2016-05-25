"""Simulation stats container."""

import logging

import injector
import numpy

from activity_distribution import TrainingDistribution
from base import Base
from histogram import Histogram
from module import Binder
from module import CustomInjector
from static import weighted_user_satisfaction

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@injector.singleton
@injector.inject(_training_distribution=TrainingDistribution)
# pylint: disable=no-member
class Stats(Base):
    """This is just a singleton dict with some helpers."""

    def __init__(self):
        super(Stats, self).__init__()
        self.__builder = CustomInjector(Binder()).get(
            injector.AssistedBuilder(cls=Histogram))
        self.__default_timeout = self.get_config_int('default_timeout')
        self.__satisfaction_threshold = self.get_config_int(
            'satisfaction_threshold', section='stats')
        self.__storage = {}

    def _idle_timeout(self, cid=None):
        """Indicates the global idle timeout."""
        if cid is None:
            return self._training_distribution.global_idle_timeout()
        return self._training_distribution.optimal_idle_timeout(cid)

    def user_satisfaction(self):
        """Calculates de user satisfaction."""
        lst = []
        for cid in self._training_distribution.servers:
            count = self.count_histogram('INACTIVITY_TIME', cid)
            if count > 0:
                lst.append(
                    sum(weighted_user_satisfaction(i, self._idle_timeout(cid),
                                                   self.__satisfaction_threshold)
                        for i in self.get_all_histogram('INACTIVITY_TIME', cid))
                    / count * 100)
        return numpy.mean(lst)

    def removed_inactivity(self):
        """Calculates how much inactive has been removed."""
        return (sum(i - self._idle_timeout()
                    for i in self.get_all_histogram('INACTIVITY_TIME')
                    if i > self._idle_timeout())
                / self.sum_histogram('INACTIVITY_TIME') * 100)

    def append(self, key, value, cid, timestamp=None):
        """Inserts a new value for a key at now.."""
        if key not in self.__storage:
            self.__storage[key] = self.__builder.build(name=key)
        if timestamp is None:
            timestamp = self._env.now
        self.__storage[key].append(timestamp, cid, value)

    def get_all_hourly_histograms(self, key):
        """Gets all the subhistograms per hour."""
        return self.__storage[key].get_all_hourly_histograms()

    def get_all_hourly_summaries(self, key):
        """Gets all the summaries per hour."""
        return self.__storage[key].get_all_hourly_summaries()

    def get_all_histogram(self, key, cid=None):
        """Gets all of the histogram data."""
        return self.__storage[key].get_all_histogram(cid)

    def get_all_hourly_count(self, key):
        """Gets all the count per hour."""
        return self.__storage[key].get_all_hourly_count()

    def sum_histogram(self, key, cid=None):
        """Sums one histogram elements."""
        try:
            return self.__storage[key].sum_histogram(cid)
        except KeyError:
            return 0.0

    def count_histogram(self, key, cid=None):
        """Counts one histogram elements."""
        try:
            return self.__storage[key].count_histogram(cid)
        except KeyError:
            return 0
