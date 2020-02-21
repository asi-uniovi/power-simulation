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

"""Module to generate fleets based on very high level parameters."""

import math
import numpy
import typing
import scipy.stats
from simulation.base import Base
from simulation.static import draw_from_distribution
from simulation.static import generate_servers
from simulation.static import HISTOGRAMS
from simulation.static import timestamp_to_day


def norm(m: float, s: float = None) -> scipy.stats.norm:
    """Normal distribution with expected mean and std of m and s."""
    if s is None:
        s = m / 100
    return scipy.stats.norm(loc=m, scale=s)


def lognorm(m: float, s: float = None) -> scipy.stats.lognorm:
    """log-Normal distribution with expected mean and std of m and s.

    This is a little wrapper for SciPy's lognorm that creates it in the way
    that its mean will be m and its standard deviation s.
    """
    if s is None:
        s = m / 100
    m2 = m**2
    phi = math.sqrt(s**2 + m2)
    sigma = math.sqrt(math.log(phi**2 / m2))
    return scipy.stats.lognorm(s=sigma, loc=0, scale=(m2 / phi))


N = 1000
IN_TIME = 9
LUNCH_TIME = 13
OUT_TIME = 17
SMALL_SHUTDOWN = 3600
OFF_FRACTION = 0.01
OFF_FRACTION_NIGHT = 0.8
DISTRIBUTION = lognorm
ACTIVITY = 900
INACTIVITY = 1800


class FleetGenerator(Base):
    """Geenerates a fleet based on high level parameters.

    This class has the same same interface as ActiviyDistribution, but instead
    it generates the timeout and (in)activity based on these other parameters.
    """

    def __init__(self):
        """Constructs the simulated fleet.

        Args:
          nservers: int, number of servers to simulate.
          in_hour: int, the time of starting working.
          out_hour: int, the time of leaving work.
        """
        super(FleetGenerator, self).__init__()
        self.__target_satisfaction = self.get_config_int('target_satisfaction')
        self.__servers = generate_servers(self.users_num)

    @property
    def servers(self) -> typing.List[str]:
        """Just return the generated servers."""
        return self.__servers

    def global_idle_timeout(self) -> float:
        """Timeout is infinite, since it is calculated a posteriori."""
        return math.inf

    def optimal_idle_timeout(
            self, cid: str, all_timespan: bool = False) -> float:
        """The timeout is unique in this setup."""
        return self.global_idle_timeout()

    def random_activity_for_timestamp(self, cid: str, timestamp: int) -> float:
        """Activity is always a log-normal."""
        return draw_from_distribution(
            self._get_distribution(cid, 'ACTIVITY_TIME', timestamp))

    def random_inactivity_for_timestamp(
            self, cid: str, timestamp: int) -> float:
        """Inactivity is always a log-normal."""
        return draw_from_distribution(
            self._get_distribution(cid, 'INACTIVITY_TIME', timestamp))

    def off_interval_for_timestamp(self, cid: str, timestamp: int) -> float:
        """Off interval for a given simulation timestamp."""
        return draw_from_distribution(
            self._get_distribution(cid, 'USER_SHUTDOWN_TIME', timestamp))

    def off_frequency_for_hour(self, cid: str, day: int, hour: int) -> float:
        """Shutdown frequency for a given simulation hour."""
        if day in (0, 6) or hour >= OUT_TIME:
            return OFF_FRACTION_NIGHT
        return OFF_FRACTION

    def get_all_hourly_percentiles(
            self, key: str, percentile: float) -> typing.List[float]:
        """Returns the requested percentile per hour."""
        percentiles = []
        transposed = self.get_all_hourly_distributions()[key]
        for day in range(7):
            for hour in range(24):
                try:
                    percentiles.append(numpy.percentile(
                        [i for i in transposed.get(day, {}).get(hour, [])],
                        percentile))
                except IndexError:
                    percentiles.append(0.0)
        return percentiles

    def get_all_hourly_count(self, key: str) -> typing.List[int]:
        """There is a fixed amount of events, N."""
        return [N] * 168

    def get_all_hourly_distributions(self):
        """Returns all the intervals per day, hour and key."""
        transposed = {}
        for key in HISTOGRAMS:
            keys = transposed.setdefault(key, {})
            for day in range(7):
                days = keys.setdefault(day, {})
                for hour in range(24):
                    distr = self._get_distribution(
                        None, key, day=day, hour=hour)
                    days.setdefault(hour, [
                        abs(distr.rvs()) for _ in range(N) if distr])
        return transposed

    def _get_distribution(self, cid: str, key: str, timestamp: int = None,
                          day: int = None, hour: int = None):
        """Resolve a key to a distribution."""
        if key == 'USER_SHUTDOWN_TIME':
            return self._user_shutdown_time(cid, timestamp, day, hour)
        elif key == 'AUTO_SHUTDOWN_TIME':
            return None
        elif key == 'ACTIVITY_TIME':
            return self._activity_time(timestamp, day, hour)
        elif key == 'INACTIVITY_TIME':
            return self._inactivity_time(cid, timestamp, day, hour)
        raise ValueError('Invalid key for _get_distribution(): %s', key)

    def _activity_time(self, timestamp: int = None, day: int = None,
                       hour: int = None):
        """Distribution for the activity by the user."""
        if timestamp is not None:
            day, hour = timestamp_to_day(timestamp)
        return DISTRIBUTION(ACTIVITY, 600)

    def _inactivity_time(self, cid: str, timestamp: int = None,
                         day: int = None, hour: int = None):
        """Distribution for the inactivity by the user."""
        if timestamp is not None:
            day, hour = timestamp_to_day(timestamp)
        return DISTRIBUTION(INACTIVITY, 600)

    def _user_shutdown_time(self, cid: str, timestamp: int = None,
                            day: int = None, hour: int = None):
        """Distribution for the shutdown triggered by the user."""
        if timestamp is not None:
            day, hour = timestamp_to_day(timestamp)
        if day not in (0, 6):
            if hour <= IN_TIME or hour >= OUT_TIME:
                return self._user_shutdown_time_prob(cid, day, hour, 0.1)
            return self._user_shutdown_time_prob(cid, day, hour, 0.7)
        return self._user_shutdown_time_prob(cid, day, hour, 0.05)

    def _user_shutdown_time_prob(
            self, cid: str, day: int, hour: int, short: float):
        """Resolves the shutdown profile based on the probability per event."""
        if scipy.rand() <= short:
            return DISTRIBUTION(SMALL_SHUTDOWN, 900)
        return self._user_shutdown_time_next_in_time(cid, day, hour)

    def _user_shutdown_time_next_in_time(self, cid: str, day: int, hour: int):
        """Shutdown time for next IN_TIME."""
        time_left = int(24 - hour + IN_TIME) * 3600
        if day == 5:
            return DISTRIBUTION(time_left + 48 * 3600, 1800)
        return DISTRIBUTION(time_left, 1800)
