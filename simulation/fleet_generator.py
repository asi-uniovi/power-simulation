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

import functools
import math
import typing
import scipy.stats
from simulation.base import Base
from simulation.static import timestamp_to_day

USERS = 100
IN_TIME = 8
OUT_TIME = 17


def _generate_servers(size: int) -> typing.List[str]:
    """Generates a list of servers randomly generated."""
    fill = math.ceil(math.log(size, 10))
    return ['workstation' + str(i).zfill(fill) for i in range(size)]


# pylint: disable=invalid-name,no-member
def norm(m: float, s: float = None) -> scipy.stats.norm:
    """Normal distribution with expected mean and std of m and s."""
    if s is None:
        s = m / 4
    return scipy.stats.norm(loc=m, scale=s)


# pylint: disable=invalid-name,no-member
def lognorm(m: float, s: float = None) -> scipy.stats.lognorm:
    """log-Normal distribution with expected mean and std of m and s.

    This is a little wrapper for SciPy's lognorm that creates it in the way that
    its mean will be m and its standard deviation s."""
    if s is None:
        s = m / 4
    m2 = m**2
    phi = math.sqrt(s**2 + m2)
    sigma = math.sqrt(math.log(phi**2 / m2))
    return scipy.stats.lognorm(s=sigma, loc=0, scale=(m2 / phi))


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
        self.__empty_servers = []
        self.__servers = _generate_servers(USERS)

    @property
    def servers(self) -> typing.List[str]:
        """Just return the generated servers."""
        return self.__servers

    @property
    def empty_servers(self) -> typing.List[str]:
        """There are not generated servers in this fleet."""
        return self.__empty_servers

    def intersect(self, other: 'FleetGenerator') -> None:
        """Make this activity distribution intersect with other."""
        to_remove = set(self.empty_servers) | set(other.empty_servers)
        to_remove |= set(self.servers) ^ set(other.servers)
        self.remove_servers(to_remove)
        other.remove_servers(to_remove)

    def remove_servers(self, empty_servers: typing.List[str]) -> None:
        """Remove servers and mark them as empty."""
        self.__empty_servers = set(self.__empty_servers) | set(empty_servers)
        self.__servers = sorted(set(self.__servers) - self.__empty_servers)
        self.__empty_servers = sorted(self.__empty_servers)

    # pylint: disable=no-self-use
    def global_idle_timeout(self) -> float:
        """Timeout is infinite, since it is calculated a posteriori."""
        return math.inf

    # pylint: disable=unused-argument
    def optimal_idle_timeout(
            self, cid: str, all_timespan: bool = False) -> float:
        """The timeout is unique in this setup."""
        return self.global_idle_timeout()

    # pylint: disable=unused-argument
    def random_activity_for_timestamp(self, cid: str, timestamp: int) -> float:
        """Activity is always a log-normal."""
        distribution = self._get_distribution('ACTIVITY_TIME')
        act = distribution.rvs()
        while act <= 0:
            act = distribution.rvs()
        return act

    def random_inactivity_for_timestamp(
            self, cid: str, timestamp: int) -> float:
        """Inactivity is always a log-normal."""
        distribution = self._get_distribution('INACTIVITY_TIME')
        act = distribution.rvs()
        while act <= 0:
            act = distribution.rvs()
        return act

    def off_interval_for_timestamp(self, cid: str, timestamp: int) -> float:
        """Off interval for a given simulation timestamp."""
        distribution = self._get_distribution('USER_SHUTDOWN_TIME', timestamp)
        act = distribution.rvs()
        while act <= 0:
            act = distribution.rvs()
        return act

    def off_frequency_for_hour(self, cid: str, day: int, hour: int) -> float:
        """Shutdown frequency for a given simulation hour."""
        fraction = 0.01
        if 1 <= day <= 5 and IN_TIME <= hour < OUT_TIME:
            fraction = 0.05
        if 1 <= day <= 5 and hour == OUT_TIME:
            fraction = 0.95
        return norm(m=fraction * len(self.servers),
                    s=math.sqrt(len(self.servers))).rvs()

    def get_all_hourly_summaries(
            self, _, summaries: dict = ('mean', 'median')
    ) -> typing.List[typing.Dict[str, float]]:
        """There are just no events per hour, therefore return 0s."""
        s = {s: 0.0 for s in summaries}
        return [s] * 168

    def get_all_hourly_count(self, key: str) -> typing.List[int]:
        """There are just no events per hour, therefore return 0s."""
        return [0] * 168

    @functools.lru_cache()
    def _get_distribution(self, key, timestamp: int = None):
        if key == 'USER_SHUTDOWN_TIME':
            return self._user_shutdown_time(timestamp)
        elif key == 'AUTO_SHUTDOWN_TIME':
            raise NotImplementedError
        elif key == 'ACTIVITY_TIME':
            return lognorm(m=600)
        elif key == 'INACTIVITY_TIME':
            return lognorm(m=3600)
        elif key == 'IDLE_TIME':
            raise NotImplementedError
        raise ValueError('Invalid key for _get_distribution(): %s', key)

    def _user_shutdown_time(self, timestamp: int):
        """Generates the distribution for the shutdown triggered by the user."""
        day, hour = timestamp_to_day(timestamp)
        if day in (0, 6):
            return self._user_shutdown_time_weekend(day, hour)
        return self._user_shutdown_time_week(day, hour)

    def _user_shutdown_time_week(self, day: int, hour: int):
        """Week shutdown time."""
        if hour < 10:
            return self._user_shutdown_time_week_prob(
                day, hour, 0.8, 0.9, 1.0)
        if hour < 12:
            return self._user_shutdown_time_week_prob(
                day, hour, 0.05, 0.95, 1.0)
        if hour < 16:
            return self._user_shutdown_time_week_prob(
                day, hour, 0.9, 0.9, 0.95)
        return self._user_shutdown_time_week_prob(
            day, hour, 0.05, 0.05, 0.95)

    # pylint: disable=too-many-arguments
    def _user_shutdown_time_week_prob(
            self, day: int, hour: int, short: float, midday: float,
            next_in_time: float):
        """Resolves the shutdown profile based on the probability per event."""
        rnd = scipy.rand()
        if rnd <= short:
            return lognorm(300, 60)
        if rnd <= midday:
            return self._user_shutdown_time_midday(day, hour)
        if rnd <= next_in_time:
            return self._user_shutdown_time_next_in_time(day, hour)
        return self._user_shutdown_time_next_midday(day, hour)

    def _user_shutdown_time_midday(self, _, hour: int):
        """Shutdown time for today's mid day."""
        assert hour < 12
        return norm((12 - hour) * 3600)

    def _user_shutdown_time_next_in_time(self, day: int, hour: int):
        """Shutdown time for next IN_TIME."""
        time_left = int(24 - hour + IN_TIME) * 3600
        if day == 5:
            return norm(time_left + 48 * 3600, 3600)
        return norm(time_left)

    def _user_shutdown_time_next_midday(self, day: int, hour: int):
        """Shutdown time for next midday."""
        time_left = int(24 - hour + 12) * 3600
        if day == 5:
            return norm(time_left + 48 * 3600, 3600)
        return norm(time_left)

    def _user_shutdown_time_weekend(self, day: int, hour: int):
        """Weekend shutdown time."""
        time_left = int((day / 6) * 24 + (24 - hour + IN_TIME)) * 3600
        return norm(time_left)
