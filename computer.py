"""A simulation process of the computer."""

import enum
import injector
import logging

from activity_distribution import ActivityDistribution
from agent import Agent
from base import Base
from stats import Stats

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@injector.inject(_activity_distribution=ActivityDistribution,
                 _agent=Agent,
                 _stats=Stats)
class Computer(Base):
    """A simple server.

    Server with configurable exponential serving rate.
    """

    def __init__(self):
        super(Computer, self).__init__()
        self._serving_rate = self.get_config_float('serving_rate')
        self._monitoring_interval = self.get_config_int('monitoring_interval')
        self._last_user_access = self._env.now
        self.off_event = self._env.event()
        self._env.process(self.__monitor_loop())
        self._env.process(self.__off_loop())

    @property
    def serving_time(self):
        """Exponential serving time based on serving ratio."""
        # pylint: disable=no-member
        time = self._activity_distribution.random_activity_for_timestamp(
            self._env.now)
        logger.debug('Activity time: %f', time)
        self._stats.append('ACTIVITY_TIME', time)
        return time

    @property
    def inactivity(self):
        """This simulates Window's LastUserTime()."""
        return self._env.now - self._last_user_access

    def serve(self):
        """Serve and count the amount of requests completed."""
        self._last_user_access = self._env.now
        yield self._env.timeout(self.serving_time) & self.off_event

    def __monitor_loop(self):
        """Runs the monitoring loop for this server."""
        while True:
            logger.debug('__monitor_loop running')
            self._stats.append('INACTIVITY_TIME_MONITORED', self.inactivity)
            yield self._env.timeout(self._monitoring_interval)

    def __off_loop(self):
        """Runs the loop that turns the server off."""
        while True:
            logger.debug('__off_loop running (%d)', self._env.now)
            if self._agent.indicate_shutdown():
                logger.debug('Shutting down PC.')
                shutdown_time = self._agent.shutdown_interval()
                self._stats.append('SHUTDOWN_TIME', shutdown_time)
                yield self._env.timeout(shutdown_time)
                self.off_event.succeed()
                self.off_event = self._env.event()
            else:
                self._env.step()
