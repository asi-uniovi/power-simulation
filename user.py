"""User simulation process."""

import logging
from base import Base
from request import Request
from stats import Stats

logger = logging.getLogger(__name__)


class User(Base):
    """A user model.

    This class generates requests to the system randomly, based on:
      - A distribution of arrival times: defaults to exponential.
      - The average interarrival time.
    """

    def __init__(self, config, env, server, activity_distribution):
        logger.debug('New User')
        super(User, self).__init__(config)
        self._env = env
        self._server = server
        self._stats = Stats()
        self._activity_distribution = activity_distribution

    @property
    def interarrival_time(self):
        time = self._activity_distribution.random_inactivity_for_timestamp(
            self._env.now)
        logger.debug('Interarrival time: %f', time)
        self._stats.append('INACTIVITY_TIME', time)
        return time

    def run(self):
        """Generates requests af the defined frequency."""
        while True:
            self._env.process(
                Request(self._config, self._env, self._server).run())
            yield self._env.timeout(self.interarrival_time)
