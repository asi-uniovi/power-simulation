"""Module to generate fleets based on very high level parameters."""

import functools
import math
import typing
import scipy.stats
from simulation.base import Base

USERS = 100
IN_TIME = 8
OUT_TIME = 15


def _generate_servers(size: int) -> typing.List[str]:
    """Generates a list of servers randomly generated."""
    fill = math.ceil(math.log(size, 10))
    return ['workstation' + str(i).zfill(fill) for i in range(size)]


# pylint: disable=invalid-name,no-member
def lognorm(m, s):
    """log-Normal distribution with expected mean and std of m and s.

    This is a little wrapper for SciPy's lognorm that creates it in the way that
    its mean will be m and its standard deviation s."""
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

    def global_idle_timeout(self) -> float:
        """Global idle timeout for the log-normal inactivity distribution."""
        return self._get_distribution('INACTIVITY_TIME').ppf(
            self.__target_satisfaction / 100)

    # pylint: disable=unused-argument
    def optimal_idle_timeout(self, cid: str, all_timespan: bool=False) -> float:
        """The timeout is unique in this setup."""
        return self.global_idle_timeout()

    # pylint: disable=unused-argument,no-self-use
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
        distribution = self._get_distribution('USER_SHUTDOWN_TIME')
        act = distribution.rvs()
        while act <= 0:
            act = distribution.rvs()
        return act

    def off_frequency_for_hour(self, cid: str, day: int, hour: int) -> float:
        """Shutdown frequency for a given simulation hour."""
        if day < 5 and IN_TIME < hour < OUT_TIME:
            return 0.1 * len(self.servers)
        if day < 5 and hour == OUT_TIME:
            return 0.3 * len(self.servers)
        return 0.0

    def get_all_hourly_summaries(
            self, key: str, summaries: dict=('mean', 'median')
    ) -> typing.List[typing.Dict[str, float]]:
        """Gives back all of the hourly summaries."""
        distr = self._get_distribution(key)
        s = {s: getattr(distr, s)() for s in summaries}
        return [s] * 168

    def get_all_hourly_count(self, key: str) -> typing.List[int]:
        """There are just no events per hour, therefore return 0s."""
        return [0] * 168

    @functools.lru_cache()
    def _get_distribution(self, key):
        if key == 'USER_SHUTDOWN_TIME':
            return lognorm(m=8*3600, s=2*3600)
        elif key == 'AUTO_SHUTDOWN_TIME':
            raise NotImplementedError
        elif key == 'ACTIVITY_TIME':
            return lognorm(m=1800, s=1800)
        elif key == 'INACTIVITY_TIME':
            return lognorm(m=3600, s=1800)
        elif key == 'IDLE_TIME':
            raise NotImplementedError
        raise ValueError('Invalid key for _get_distribution(): %s', key)
