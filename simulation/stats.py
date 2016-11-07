"""Simulation stats container."""

import logging
import typing
import injector
import numpy
from simulation.activity_distribution import TrainingDistribution
from simulation.base import Base
from simulation.histogram import Histogram
from simulation.static import weighted_user_satisfaction

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@injector.singleton
class Stats(Base):
    """This is just a singleton dict with some helpers."""

    @injector.inject
    def __init__(self, training_distribution: TrainingDistribution,
                 historgram_builder: injector.AssistedBuilder[Histogram]):
        super(Stats, self).__init__()
        self.__training_distribution = training_distribution
        self.__histogram_builder = historgram_builder
        self.__default_timeout = self.get_config_int('default_timeout')
        self.__satisfaction_threshold = self.get_config_int(
            'satisfaction_threshold', section='stats')
        self.__storage = {}

    def _idle_timeout(self, cid: str=None) -> float:
        """Indicates the global idle timeout."""
        if cid is None:
            return self.__training_distribution.global_idle_timeout()
        return self.__training_distribution.optimal_idle_timeout(cid)

    def reset(self) -> None:
        """Reset all stats."""
        for i in self.__storage.values():
            i.truncate()

    def user_satisfaction(self) -> float:
        """Calculates de user satisfaction."""
        lst = []
        for cid in self.__training_distribution.servers:
            count = self.count_histogram('INACTIVITY_TIME', cid)
            if count > 0:
                lst.append(
                    sum(weighted_user_satisfaction(
                        i,
                        self._idle_timeout(cid),
                        self.__satisfaction_threshold)
                        for i in self.get_all_histogram('INACTIVITY_TIME', cid))
                    / count * 100)
        return numpy.mean(lst)

    def removed_inactivity(self) -> float:
        """Calculates how much inactive has been removed."""
        return (sum(i - self._idle_timeout()
                    for i in self.get_all_histogram('INACTIVITY_TIME')
                    if i > self._idle_timeout())
                / self.sum_histogram('INACTIVITY_TIME') * 100)

    def append(self, key: str, value: float, cid: str,
               timestamp: int=None) -> None:
        """Inserts a new value for a key at now.."""
        if key not in self.__storage:
            self.__storage[key] = self.__histogram_builder.build(name=key)
        if timestamp is None:
            timestamp = self._config.env.now
        self.__storage[key].append(timestamp, cid, value)

    def get_all_hourly_histograms(self, key: str) -> typing.List[numpy.ndarray]:
        """Gets all the subhistograms per hour."""
        return self.__storage[key].get_all_hourly_histograms()

    def get_all_hourly_summaries(
            self, key: str) -> typing.List[typing.Dict[str, float]]:
        """Gets all the summaries per hour."""
        return self.__storage[key].get_all_hourly_summaries()

    def get_all_histogram(self, key: str, cid: str=None) -> numpy.ndarray:
        """Gets all of the histogram data."""
        return self.__storage[key].get_all_histogram(cid)

    def get_all_hourly_count(self, key: str) -> typing.List[int]:
        """Gets all the count per hour."""
        return self.__storage[key].get_all_hourly_count()

    def sum_histogram(self, key: str, cid: str=None) -> float:
        """Sums one histogram elements."""
        try:
            return self.__storage[key].sum_histogram(cid)
        except KeyError:
            return 0.0

    def count_histogram(self, key: str, cid: str=None) -> int:
        """Counts one histogram elements."""
        try:
            return self.__storage[key].count_histogram(cid)
        except KeyError:
            return 0
