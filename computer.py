"""A simulation process of the computer."""

import enum
import logging

import injector
import simpy

from activity_distribution import ActivityDistribution
from base import Base
from stats import Stats

logger = logging.getLogger(__name__)


@enum.unique
class ComputerStatus(enum.Enum):
    on = 1
    stand_by = 2
    hibernated = 3
    off = 4


@injector.inject(_activity_distribution=ActivityDistribution,
                 _stats=Stats)
class Computer(Base):
    """A simple server.

    Server with configurable exponential serving rate.
    """

    def __init__(self):
        super(Computer, self).__init__()
        self._status = ComputerStatus.on
        self._idle_timeout = self.get_config_int(
            'idle_timeout', section='computer')
        self._idle_timer = self._env.process(self.idle_timer())
        self._last_user_access = self._env.now
        self._last_auto_shutdown = self._env.now

    def change_status(self, status):
        logger.debug('change status %s -> %s', self._status, status)
        if status == ComputerStatus.on:
            self._stats.append('AUTO_SHUTDOWN_TIME',
                               self._env.now - self._last_auto_shutdown)
        self._status = status

    @property
    def serving_time(self):
        """Exponential serving time based on serving ratio."""
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
        if self._status != ComputerStatus.on:
            self.change_status(ComputerStatus.on)
        self._last_user_access = self._env.now
        if self._idle_timer.is_alive:
            self._idle_timer.interrupt()
        self._idle_timer = self._env.process(self.idle_timer())
        yield self._env.timeout(self.serving_time)

    def idle_timer(self):
        while True:
            try:
                idle_start = self._env.now
                yield self._env.timeout(self._idle_timeout)
                self._stats.append('IDLE_TIMEOUT', self._idle_timeout)
                self.change_status(ComputerStatus.off)
                self._last_auto_shutdown = self._env.now
            except simpy.Interrupt:
                pass
            finally:
                self._stats.append('IDLE_TIME', self._env.now - idle_start)
                self._env.exit()
