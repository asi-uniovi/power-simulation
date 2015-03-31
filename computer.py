"""A simulation process of the computer."""

import injector
import logging
import numpy

from base import Base
from stats import Stats

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Computer(Base):
    """A simple server.

    Server with configurable exponential serving rate.
    """

    @injector.inject(stats=Stats)
    def __init__(self, stats):
        super(Computer, self).__init__()
        self._stats = stats
        self._serving_rate = self.get_config_float('serving_rate')
        self._monitoring_interval = self.get_config_int('monitoring_interval')
        self._last_user_access = self._env.now
        self._env.process(self.__monitor_loop())

    @property
    def serving_time(self):
        """Exponential serving time based on serving ratio."""
        # pylint: disable=no-member
        time = numpy.random.exponential(1.0 / self._serving_rate)
        self._stats.increment('SERVING_TIME', time)
        logger.debug('Serving time: %f', time)
        return time

    @property
    def inactivity(self):
        """This simulates Window's LastUserTime()."""
        return self._env.now - self._last_user_access

    def serve(self):
        """Serve and count the amount of requests completed."""
        self._last_user_access = self._env.now
        yield self._env.timeout(self.serving_time)
        self._stats.increment('SERVED_REQUESTS')

    def __monitor_loop(self):
        """Runs the monitoring loop for this server."""
        while True:
            self._stats.add_to_bin(
                'INACTIVITY_TIME_MONITORED', self.inactivity)
            yield self._env.timeout(self._monitoring_interval)
