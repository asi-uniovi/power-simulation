"""A simulation of the computer."""

import logging
import numpy
from base import Base
from stats import Stats

logger = logging.getLogger(__name__)


class Server(Base):
    """A simple server.

    Server with configurable exponential serving rate.
    """

    def __init__(self, config, env):
        logger.debug('New server')
        super(Server, self).__init__(config)
        self._stats = Stats()
        self._env = env
        self._serving_rate = self.get_config_float('serving_rate')
        self._monitoring_interval = self.get_config_int('monitoring_interval')
        # Start the monitoring loop as soon as the server is running.
        self._env.process(self.__monitor_loop())

    @property
    def serving_time(self):
        """Exponential serving time based on serving ratio."""
        time = numpy.random.exponential(1.0 / self._serving_rate)
        logger.debug('Serving time: %f', time)
        return time

    def serve(self):
        """Serve and count the amount of requests completed."""
        yield self._env.timeout(self.serving_time)
        self._stats.increment('SERVED_REQUESTS')

    def __monitor_loop(self):
        """Runs the monitoring loop for this server."""
        while True:
            logger.debug('Server monitoring loop (%d)', self._env.now)
            yield self._env.timeout(self._monitoring_interval)
