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

"""User simulation process."""

import injector
import numpy
from simulation.activity_distribution import DistributionFactory
from simulation.activity_distribution import timestamp_to_day
from simulation.computer import Computer
from simulation.computer import ComputerStatus
from simulation.configuration import Configuration
from simulation.stats import Stats


class User(object):
    """A user model.

    This class generates requests to the system randomly, based on:
      - A distribution of arrival times: defaults to exponential.
      - The average interarrival time.
    """

    @injector.inject
    @injector.noninjectable('cid')
    def __init__(
            self, config: Configuration,
            computer_builder: injector.ClassAssistedBuilder[Computer],
            distr_factory: DistributionFactory, stats: Stats, cid: str):
        super(User, self).__init__()
        self.__computer = computer_builder.build(cid=cid)
        self.__activity_distribution = distr_factory()
        self.__stats = stats
        self.__current_hour = None
        self.__off_frequency = None
        self.__config = config

    def run(self) -> None:
        """Generates requests af the defined frequency."""
        while True:
            if self.__indicate_shutdown():
                shutdown_time = self.__shutdown_interval()
                self.__computer.change_status(ComputerStatus.off)
                self.__stats.append(
                    'USER_SHUTDOWN_TIME', shutdown_time, self.__computer.cid)
                yield self.__config.env.timeout(shutdown_time)
            yield self.__config.env.process(self.__computer.serve())
            inactivity_time = (self.__activity_distribution
                               .random_inactivity_for_timestamp(
                                   self.__computer.cid, self.__config.now))
            self.__stats.append(
                'INACTIVITY_TIME', inactivity_time, self.__computer.cid)
            yield self.__config.env.timeout(inactivity_time)

    def __indicate_shutdown(self) -> bool:
        """Indicates whether we need to shutdown or not."""
        if not self.__computer.is_on:
            return False
        hour = timestamp_to_day(self.__config.now)
        if self.__current_hour != hour:
            self.__current_hour = hour
            self.__off_frequency = (
                self.__activity_distribution.off_frequency_for_hour(
                    self.__computer.cid, *hour))
        if self.__off_frequency > numpy.random.random():
            self.__off_frequency -= 1.0
            return True
        return False

    def __shutdown_interval(self) -> float:
        """Generates shutdown interval lengths."""
        return numpy.around(
            self.__activity_distribution.off_interval_for_timestamp(
                self.__computer.cid, self.__config.now))
