"""A simulation of the computer."""

from base import Base
from stats import Stats
import numpy


class Server(Base):
    """A simple server.

    Server with configurable exponential serving rate.
    """

    def __init__(self, config, env):
        super(Server, self).__init__(config)
        self._stats = Stats()
        self._env = env
        self._serving_rate = self.get_config_float('serving_rate')

    @property
    def serving_time(self):
        """Exponential serving time based on serving ratio."""
        return numpy.random.exponential(1.0 / self._serving_rate)

    def serve(self):
        """Serve and count the amount of requests completed."""
        yield self._env.timeout(self.serving_time)
        self._stats.increment('SERVED_REQUESTS')
