"""User simulation process."""

import logging

import injector
import numpy

from activity_distribution import ActivityDistribution
from activity_distribution import timestamp_to_day
from base import Base
from computer import Computer, ComputerStatus
from stats import Stats

logger = logging.getLogger(__name__)


@injector.inject(_activity_distribution=ActivityDistribution,
                 _stats=Stats,
                 _computer=Computer)
class User(Base):
    """A user model.

    This class generates requests to the system randomly, based on:
      - A distribution of arrival times: defaults to exponential.
      - The average interarrival time.
    """

    def __init__(self):
        super(User, self).__init__()
        self.__current_hour = None
        self.__shutdown_fraction = None

    def run(self):
        """Generates requests af the defined frequency."""
        while True:
            yield self._env.process(self._computer.serve())
            assert self._computer.status == ComputerStatus.on
            now = self._env.now
            if self.__indicate_shutdown():
                logger.debug('User is shutting down PC %s', self._computer.cid)
                shutdown_time = self.__shutdown_interval()
                self._computer.change_status(ComputerStatus.off)
                yield self._env.timeout(shutdown_time)
                self._stats.append('USER_SHUTDOWN_TIME', shutdown_time,
                                   self._computer.cid, timestamp=now)
            else:
                inactivity_time = (
                    self._activity_distribution.random_inactivity_for_timestamp(
                        self._computer.cid, self._env.now))
                assert inactivity_time > 0, inactivity_time
                yield self._env.timeout(inactivity_time)
                self._stats.append('INACTIVITY_TIME', inactivity_time,
                                   self._computer.cid, timestamp=now)

    def __indicate_shutdown(self):
        """Indicates whether we need to shutdown or not."""
        hour = timestamp_to_day(self._env.now)
        if self.__current_hour != hour:
            self.__current_hour = hour
            self.__shutdown_fraction = (
                self._activity_distribution.off_fraction_for_hour(
                    self._computer.cid, *hour))
            assert self.__shutdown_fraction >= 0
        if self.__shutdown_fraction > 0:
            self.__shutdown_fraction -= 1
            return True
        return False

    def __shutdown_interval(self):
        """Generates shutdown interval lengths."""
        try:
            shutdown = numpy.ceil(
                self._activity_distribution.off_interval_for_timestamp(
                    self._computer.cid, self._env.now))
            assert shutdown > 0, shutdown
            return shutdown
        except TypeError:
            return 0
