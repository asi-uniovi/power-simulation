"""A simulation process of the computer."""

import enum
import logging

import injector
import simpy

from activity_distribution import ActivityDistribution
from activity_distribution import TrainingDistribution
from base import Base
from stats import Stats

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@enum.unique
# pylint: disable=invalid-name
class ComputerStatus(enum.Enum):
    """States of a computer along the simulation."""
    on = 1
    stand_by = 2
    hibernated = 3
    off = 4


@injector.inject(_activity_distribution=ActivityDistribution,
                 _training_distribution=TrainingDistribution,
                 _stats=Stats)
# pylint: disable=no-member
class Computer(Base):
    """A simple server.

    Server with configurable exponential serving rate.
    """
    __computer_id_count = -1

    def __init__(self):
        super(Computer, self).__init__()
        self.__computer_id = self._training_distribution.servers[
            Computer.__new_computer_id()]
        self.__status = ComputerStatus.on
        self.__last_auto_shutdown = None
        self.__idle_timer = self._env.process(self.__idle_timer_runner())

    @property
    def status(self):
        """Indicates the computer status."""
        return self.__status

    @property
    def cid(self):
        """Read only computer ID."""
        return self.__computer_id

    def change_status(self, status, interrupt_idle_timer=True):
        """Changes the state of the computer, and takes any side action."""
        assert status != self.__status
        if interrupt_idle_timer and self.__idle_timer.is_alive:
            self.__idle_timer.interrupt()
        if (status == ComputerStatus.on
                and self.__last_auto_shutdown is not None):
            self._stats.append('AUTO_SHUTDOWN_TIME',
                               self._env.now - self.__last_auto_shutdown,
                               self.__computer_id,
                               timestamp=self.__last_auto_shutdown)
            self.__last_auto_shutdown = None
        self.__status = status

    def serve(self):
        """Serve and count the amount of requests completed."""
        if self.__status != ComputerStatus.on:
            self.change_status(ComputerStatus.on)
        if self.__idle_timer.is_alive:
            self.__idle_timer.interrupt()
        activity_time = (
            self._activity_distribution.random_activity_for_timestamp(
                self.__computer_id, self._env.now))
        assert activity_time > 0, activity_time
        now = self._env.now
        yield self._env.timeout(activity_time)
        self._stats.append('ACTIVITY_TIME', activity_time, self.__computer_id,
                           timestamp=now)
        self.__idle_timer = self._env.process(self.__idle_timer_runner())

    @property
    def __idle_timeout(self):
        """Indicates this computer idle time."""
        idle = self._training_distribution.optimal_idle_timeout(
            self.__computer_id)
        assert idle > 0, idle
        return idle

    def __idle_timer_runner(self):
        """Process for the idle timer control."""
        try:
            idle_start = self._env.now
            yield self._env.timeout(self.__idle_timeout)
            self.change_status(ComputerStatus.off,
                               interrupt_idle_timer=False)
            self.__last_auto_shutdown = self._env.now
        except simpy.Interrupt:
            pass
        finally:
            self._stats.append('IDLE_TIME', self._env.now - idle_start,
                               self.__computer_id, timestamp=idle_start)

    @classmethod
    def __new_computer_id(cls):
        """Creates a new computer ID."""
        cls.__computer_id_count += 1
        return cls.__computer_id_count
