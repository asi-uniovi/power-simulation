"""User simulation process."""

from activity_distribution import ActivityDistribution
from base import Base
from request import Request


class User(Base):
    """A user model.

    This class generates requests to the system randomly, based on:
      - A distribution of arrival times: defaults to exponential.
      - The average interarrival time.
    """

    def __init__(self, config, env, server):
        super(User, self).__init__(config)
        self._env = env
        self._server = server
        self._activity_distribution = ActivityDistribution(
            filename=self.get_config('filename', 'activity_distribution'),
            distribution=self.get_config('distribution',
                                         'activity_distribution'))

    @property
    def interarrival_time(self):
        return self._activity_distribution.random_inactivity_for_timestamp(
            self._env.now)

    def run(self):
        """Generates requests af the defined frequency."""
        while True:
            self._env.process(Request(self._config, self._env, self._server,
                                      4.0).run())
            yield self._env.timeout(self.interarrival_time)
