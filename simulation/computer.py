# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A simulation process of the computer."""

import enum
import logging
import injector
import simpy
from simulation.activity_distribution import DistributionFactory
from simulation.base import Base
from simulation.stats import Stats

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@enum.unique
class ComputerStatus(enum.Enum):
    """States of a computer along the simulation."""
    off = 0
    on = 1  # pylint: disable=invalid-name


# pylint: disable=too-many-instance-attributes
class Computer(Base):
    """A simple server.

    Server with configurable exponential serving rate.
    """

    @injector.inject
    @injector.noninjectable('cid')
    def __init__(self, distr_factory: DistributionFactory, stats: Stats,
                 cid: str):
        super(Computer, self).__init__()
        self.__activity_distribution = distr_factory()
        self.__training_distribution = distr_factory(training=True)
        self.__stats = stats
        self.__computer_id = cid
        self.__status = ComputerStatus.on
        self.__last_auto_shutdown = None
        self.__started = False
        self.__idle_timer = self.env.process(self.__idle_timer_runner())

    @property
    def cid(self) -> str:
        """Read only computer ID."""
        return self.__computer_id

    def change_status(self, status: ComputerStatus,
                      interrupt_idle_timer: bool = True) -> None:
        """Changes the state of the computer, and takes any side action."""
        if interrupt_idle_timer and self.__idle_timer.is_alive:
            self.__idle_timer.interrupt()
        if (status == ComputerStatus.on
                and self.__last_auto_shutdown is not None):
            self.__stats.append(
                'AUTO_SHUTDOWN_TIME',
                self.env.now - self.__last_auto_shutdown,
                self.__computer_id, timestamp=self.__last_auto_shutdown)
            self.__last_auto_shutdown = None
        self.__status = status

    def serve(self) -> None:
        """Serve and count the amount of requests completed."""
        if self.__status != ComputerStatus.on:
            self.change_status(ComputerStatus.on)
        if self.__idle_timer.is_alive:
            self.__idle_timer.interrupt()
        activity_time = (
            self.__activity_distribution.random_activity_for_timestamp(
                self.__computer_id, self.env.now))
        self.__stats.append(
            'ACTIVITY_TIME', activity_time, self.__computer_id)
        yield self.env.timeout(activity_time)
        self.__idle_timer = self.env.process(self.__idle_timer_runner())

    def __idle_timeout(self) -> float:
        """Indicates this computer idle time."""
        idle = self.__training_distribution.optimal_idle_timeout(
            self.__computer_id)
        return idle

    def __idle_timer_runner(self) -> None:
        """Process for the idle timer control."""
        if self.get_arg('disable_auto_shutdown'):
            return
        if not self.__started and self.get_arg('fleet_generator'):
            # If generating a random fleet, we start inactive until Monday.
            try:
                self.__started = True
                yield self.env.timeout((24 + 8) * 3600)
            except simpy.Interrupt:
                pass
        try:
            idle_timeout = self.__idle_timeout()
            self.__stats.append('IDLE_TIME', idle_timeout, self.__computer_id)
            yield self.env.timeout(idle_timeout)
            self.change_status(ComputerStatus.off,
                               interrupt_idle_timer=False)
            self.__last_auto_shutdown = self.env.now
        except simpy.Interrupt:
            pass
