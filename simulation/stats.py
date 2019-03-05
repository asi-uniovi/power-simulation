# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Simulation stats container."""

import logging
import typing
import injector
import numpy
from simulation.activity_distribution import DistributionFactory
from simulation.base import Base
from simulation.histogram import Histogram
from simulation.static import weighted_user_satisfaction

logger = logging.getLogger(__name__)


@injector.singleton
class Stats(Base):
    """This is just a singleton dict with some helpers."""

    @injector.inject
    def __init__(self, distr_factory: DistributionFactory,
                 historgram_builder: injector.AssistedBuilder[Histogram]):
        super(Stats, self).__init__()
        self.__training_distribution = distr_factory(training=True)
        self.__histogram_builder = historgram_builder
        self.__target_satisfaction = self.get_config_int('target_satisfaction')
        self.__satisfaction_threshold = self.get_config_int(
            'satisfaction_threshold')
        self.__storage = {}

    def _idle_timeout(self, cid: str = None) -> float:
        """Indicates the global idle timeout."""
        if cid is None:
            return self.__training_distribution.global_idle_timeout()
        return self.__training_distribution.optimal_idle_timeout(cid)

    def optimal_idle_timeout(self) -> float:
        """Optimal idle timeout for the simulated data (a posteriori)."""
        return numpy.percentile(self.get_all_histogram('INACTIVITY_TIME'),
                                self.__target_satisfaction)

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
        if lst:
            return numpy.mean(lst)
        return 0.0

    def apdex(self) -> float:
        """Calculates the Apdex satisfaction index."""
        satisfied, tolerating, total = 0, 0, 0
        for cid in self.__training_distribution.servers:
            timeout = self._idle_timeout(cid)
            for i in self.get_all_histogram('INACTIVITY_TIME', cid):
                if i <= timeout:
                    satisfied += 1
                elif i >= self.__satisfaction_threshold:
                    tolerating += 1
                total += 1
        return (satisfied + (tolerating / 2.0)) / total * 100

    def removed_inactivity(self) -> float:
        """Calculates how much inactive has been removed."""
        try:
            return (sum(i - self._idle_timeout()
                        for i in self.get_all_histogram('INACTIVITY_TIME')
                        if i > self._idle_timeout())
                    / self.sum_histogram('INACTIVITY_TIME') * 100)
        except ZeroDivisionError:
            return 0.0

    def append(self, key: str, value: float, cid: str,
               timestamp: int = None) -> None:
        """Inserts a new value for a key at now.."""
        if key not in self.__storage:
            self.__storage[key] = self.__histogram_builder.build(name=key)
        if timestamp is None:
            timestamp = self.env.now
        self.__storage[key].append(timestamp, cid, value)

    def get_all_hourly_histograms(self, key: str) -> typing.List[numpy.ndarray]:
        """Gets all the subhistograms per hour."""
        try:
            return self.__storage[key].get_all_hourly_histograms()
        except KeyError:
            return []

    def get_all_hourly_percentiles(
            self, key: str, percentile: float) -> typing.List[float]:
        """Gets all the percentiles per hour."""
        try:
            return self.__storage[key].get_all_hourly_percentiles(percentile)
        except KeyError:
            return [0.0] * 7 * 24

    def get_all_events(
            self, key: str, cid: str = None
    ) -> typing.List[typing.Tuple[float, float]]:
        """Gets all events on the histogram with timestamp."""
        try:
            return self.__storage[key].get_all_events(cid)
        except KeyError:
            return []

    def get_all_histogram(self, key: str, cid: str = None) -> numpy.ndarray:
        """Gets all of the histogram data."""
        try:
            return self.__storage[key].get_all_histogram(cid)
        except KeyError:
            return numpy.asarray([])

    def get_all_hourly_count(self, key: str) -> typing.List[int]:
        """Gets all the count per hour."""
        try:
            return self.__storage[key].get_all_hourly_count()
        except KeyError:
            return []

    def get_all_hourly_distributions(self):
        """Returns all the intervals per day, hour and key."""
        return {key: hist.get_all_hourly_distributions()
                for key, hist in self.__storage.items()}

    def sum_histogram(self, key: str, cid: str = None) -> float:
        """Sums one histogram elements."""
        try:
            return self.__storage[key].sum_histogram(cid)
        except KeyError:
            return 0.0

    def count_histogram(self, key: str, cid: str = None) -> int:
        """Counts one histogram elements."""
        try:
            return self.__storage[key].count_histogram(cid)
        except KeyError:
            return 0

    def flush(self):
        """Flushes all histograms stored."""
        for hist in self.__storage.values():
            hist.flush()
