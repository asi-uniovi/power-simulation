"""User simulation process."""

import injector
import logging

from activity_distribution import ActivityDistribution
from base import Base
from computer import Computer
from module import Binder, CustomInjector
from stats import Stats

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@injector.inject(_activity_distribution=ActivityDistribution,
                 _stats=Stats,
                 _computer=Computer)
class User(Base):
    """A user model.

    This class generates requests to the system randomly, based on:
      - A distribution of arrival times: defaults to exponential.
      - The average interarrival time.
    """

    @property
    def interarrival_time(self):
        """Calcualtes a random reflexion or interarrival time for the user."""
        time = self._activity_distribution.random_inactivity_for_timestamp(
            self._env.now)
        logger.debug('Inactivity time: %f', time)
        self._stats.append('INACTIVITY_TIME_ACCURATE', time)
        return time

    def run(self):
        """Generates requests af the defined frequency."""
        while True:
            yield self._env.process(self._computer.serve())
            yield self._env.timeout(self.interarrival_time)
