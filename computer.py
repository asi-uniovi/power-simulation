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
    """States of a computer along the simulation."""
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
        self._last_auto_shutdown = None
        self._idle_timer = self._env.process(self.idle_timer())

    @property
    def status(self):
        """Indicates the computer status."""
        return self._status

    @property
    def _idle_timeout(self):
        """Indicates this computer idle time."""
        return self._activity_distribution.optimal_idle_timeout

    def change_status(self, status, interrupt_idle_timer=True):
        """Changes the state of the computer, and takes any side action."""
        assert status != self.status
        logger.debug('change status %s -> %s', self._status, status)
        if interrupt_idle_timer and self._idle_timer.is_alive:
            self._idle_timer.interrupt()
        if status == ComputerStatus.on and self._last_auto_shutdown is not None:
            self._stats.append('AUTO_SHUTDOWN_TIME',
                               self._env.now - self._last_auto_shutdown,
                               timestamp=self._last_auto_shutdown)
            self._last_auto_shutdown = None
        self._status = status

    def serve(self):
        """Serve and count the amount of requests completed."""
        logger.debug('TEST of CI, revert')
        if self._status != ComputerStatus.on:
            self.change_status(ComputerStatus.on)
        if self._idle_timer.is_alive:
            self._idle_timer.interrupt()
        activity_time = (
            self._activity_distribution.random_activity_for_timestamp(
                self._env.now))
        now = self._env.now
        yield self._env.timeout(activity_time)
        self._stats.append('ACTIVITY_TIME', activity_time, timestamp=now)
        self._idle_timer = self._env.process(self.idle_timer())

    def idle_timer(self):
        """Process for the idle timer control."""
        while True:
            try:
                idle_start = self._env.now
                yield self._env.timeout(self._idle_timeout)
                self.change_status(ComputerStatus.off,
                                   interrupt_idle_timer=False)
                self._last_auto_shutdown = self._env.now
            except simpy.Interrupt:
                pass
            finally:
                self._stats.append('IDLE_TIME', self._env.now - idle_start,
                                   timestamp=idle_start)
                return
