"""User simulation process."""

import injector
import logging

from activity_distribution import ActivityDistribution
from agent import Agent
from base import Base
from computer import Computer, ComputerStatus
from stats import Stats

logger = logging.getLogger(__name__)


@injector.inject(_activity_distribution=ActivityDistribution,
                 _agent=Agent,
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
            if self._agent.indicate_shutdown():
                logger.debug('User is shutting down PC.')
                self._computer.change_status(ComputerStatus.off)
                shutdown_time = self._agent.shutdown_interval()
                self._stats.append('SHUTDOWN_TIME', shutdown_time)
                yield self._env.timeout(shutdown_time)
