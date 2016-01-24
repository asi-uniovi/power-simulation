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

    def run(self):
        """Generates requests af the defined frequency."""
        while True:
            yield self._env.process(self._computer.serve())
            assert self._computer.status == ComputerStatus.on
            if self._agent.indicate_shutdown():
                logger.debug('User is shutting down PC.')
                shutdown_time = self._agent.shutdown_interval()
                self._computer.change_status(ComputerStatus.off)
                yield self._env.timeout(shutdown_time)
                self._stats.append('USER_SHUTDOWN_TIME', shutdown_time)
            else:
                inactivity_time = (
                    self._activity_distribution.random_inactivity_for_timestamp(
                        self._env.now))
                yield self._env.timeout(inactivity_time)
                self._stats.append('INACTIVITY_TIME', inactivity_time)
