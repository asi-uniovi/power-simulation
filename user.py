"""User simulation process."""

import logging
import injector
import numpy
from activity_distribution import ActivityDistribution
from activity_distribution import timestamp_to_day
from base import Base
from computer import Computer
from computer import ComputerStatus
from stats import Stats

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class User(Base):
    """A user model.

    This class generates requests to the system randomly, based on:
      - A distribution of arrival times: defaults to exponential.
      - The average interarrival time.
    """

    @injector.inject
    def __init__(self, computer_builder: injector.AssistedBuilder[Computer],
                 activity_distribution: ActivityDistribution, stats: Stats,
                 cid: str):
        super(User, self).__init__()
        self.__computer = computer_builder.build(cid=cid)
        self.__activity_distribution = activity_distribution
        self.__stats = stats
        self.__current_hour = None
        self.__off_frequency = None

    def run(self) -> None:
        """Generates requests af the defined frequency."""
        while True:
            yield self._config.env.process(self.__computer.serve())
            now = self._config.env.now
            if self.__indicate_shutdown():
                logger.debug('User is shutting down PC %s', self.__computer.cid)
                shutdown_time = self.__shutdown_interval()
                self.__computer.change_status(ComputerStatus.off)
                yield self._config.env.timeout(shutdown_time)
                self.__stats.append('USER_SHUTDOWN_TIME', shutdown_time,
                                    self.__computer.cid, timestamp=now)
            else:
                inactivity_time = (
                    self.__activity_distribution.random_inactivity_for_timestamp(
                        self.__computer.cid, self._config.env.now))
                yield self._config.env.timeout(inactivity_time)
                self.__stats.append('INACTIVITY_TIME', inactivity_time,
                                    self.__computer.cid, timestamp=now)

    def __indicate_shutdown(self) -> bool:
        """Indicates whether we need to shutdown or not."""
        hour = timestamp_to_day(self._config.env.now)
        if self.__current_hour != hour:
            self.__current_hour = hour
            self.__off_frequency = (
                self.__activity_distribution.off_frequency_for_hour(
                    self.__computer.cid, *hour))
        if self.__off_frequency > 0:
            self.__off_frequency -= 1
            return True
        return False

    def __shutdown_interval(self) -> float:
        """Generates shutdown interval lengths."""
        try:
            shutdown = numpy.ceil(
                self.__activity_distribution.off_interval_for_timestamp(
                    self.__computer.cid, self._config.env.now))
            return shutdown
        except TypeError:
            return 0
