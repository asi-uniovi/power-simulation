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

"""A very simple simuation of several 1/M/c queuing systems."""

import injector
import logging
import math
import memory_profiler
import numpy
import scipy.stats
import sqlite3
import typing
from simulation.activity_distribution import DistributionFactory
from simulation.base import Base
from simulation.configuration import Configuration
from simulation.histogram import create_histogram_tables
from simulation.module import Module
from simulation.plot import Plot
from simulation.static import config_logging, profile, timed, WEEK
from simulation.stats import Stats
from simulation.user import User

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Simulation(Base):
    """Constructs the system and runs the simulation."""

    @injector.inject
    # pylint: disable=too-many-arguments
    def __init__(self, distr_factory: DistributionFactory,
                 user_builder: injector.AssistedBuilder[User],
                 plot: Plot, stats: Stats):
        super(Simulation, self).__init__()
        self.__activity_distribution = distr_factory()
        self.__training_distribution = distr_factory(training=True)
        self.__user_builder = user_builder
        self.__plot = plot
        self.__stats = stats
        self.target_satisfaction = self.get_config_int('target_satisfaction')
        self.__activity_distribution.intersect(self.__training_distribution)

    @property
    def servers(self) -> int:
        """Number of servers being simulated."""
        return len(self.__training_distribution.servers)

    @property
    def timeout(self) -> float:
        """Average global timeout."""
        return self.__training_distribution.global_idle_timeout()

    @timed
    def run(self) -> typing.Tuple[float, float]:
        """Sets up and starts a new simulation."""
        self.new_run()
        if self.debug:
            self.env.process(self.__monitor_time())
        for cid in self.__training_distribution.servers:
            if cid in self.__activity_distribution.servers:
                self.env.process(
                    self.__user_builder.build(cid=cid).run())
        logger.debug('Simulation starting')
        self.env.run(until=self.simulation_time)
        logger.debug('Simulation ended at %d s', self.env.now)
        self.__stats.flush()
        if self.debug:
            self.__validate_results()
        results = (self.__stats.user_satisfaction(),
                   self.__stats.removed_inactivity(),
                   self.__stats.optimal_idle_timeout())
        logger.debug('RESULT: User Satisfaction (US) = %.2f%%', results[0])
        logger.debug('RESULT: Modified Apdex = %.2f%%', self.__stats.apdex())
        logger.debug('RESULT: Removed Inactivity (RI) = %.2f%%', results[1])
        logger.debug('RESULT: Optimal idle timeout = %.2f%%', results[2])
        logger.debug('Run complete.')
        return results

    def __validate_results(self) -> None:
        """Performs vaidations on the run results and warns on errors."""
        # pylint: disable=invalid-name,no-member
        at = self.__stats.sum_histogram('ACTIVITY_TIME') / self.servers
        ust = self.__stats.sum_histogram('USER_SHUTDOWN_TIME') / self.servers
        it = self.__stats.sum_histogram('INACTIVITY_TIME') / self.servers
        val1 = abs((ust + at + it) / self.simulation_time - 1)

        if val1 > 0.1:
            logger.warning('Validation of total time failed: %.2f', val1)

    def __monitor_time(self) -> float:
        """Indicates how te simulation is progressing."""
        while True:
            logger.debug('%.2f%% completed',
                         self.env.now / self.simulation_time * 100.0)
            yield self.env.timeout(self.simulation_time / 10.0)


# pylint: disable=invalid-name
def confidence_interval(m: float, alpha: float = 0.05):
    """Generator to calculate confidence intervals in a more nicely fashion."""
    x, s, d, i = m, 0, 0, 1
    while True:
        m = yield (x, d)
        i += 1
        s = ((i - 2) / (i - 1) * s) + (1 / i * ((m - x) ** 2))
        x = ((1 - 1 / i) * x) + (1 / i * m)
        d = scipy.stats.t.interval(1 - alpha, i - 1)[1] * math.sqrt(s / i)


# pylint: disable=invalid-name,too-many-locals
@timed
def runner() -> None:
    """Bind all and launch the simulation!"""
    custom_injector = injector.Injector([Module])
    configuration = custom_injector.get(Configuration)
    config_logging(configuration)
    create_histogram_tables(custom_injector.get(sqlite3.Connection))
    if configuration.get_arg('debug'):
        numpy.random.seed(0)  # pylint: disable=no-member
    simulator = custom_injector.get(Simulation)
    max_runs = configuration.get_arg('max_runs')
    confidence_width = configuration.get_arg('max_confidence_interval_width')
    run = custom_injector.get(profile)(simulator.run)

    logger.info('Simulating %d users during %d s (%.1f week(s)).',
                simulator.servers, simulator.simulation_time,
                simulator.simulation_time / WEEK(1))
    logger.info('User Satisfaction (US) target is %d%%.',
                simulator.target_satisfaction)
    if simulator.timeout < math.inf:
        logger.info('Average global timeout will be %.2f s (%.2f min).',
                    simulator.timeout, simulator.timeout / 60)
    (s, i, t), c = run(), 1
    logger.info('Run 1: US = %.2f%%, RI = %.2f%%, timeout = %.2f', s, i, t)

    if max_runs == 1:
        logger.warning('Only one run, cannot calculate confidence intervals')
    else:
        satisfaction = confidence_interval(s)
        inactivity = confidence_interval(i)
        (xs, ds) = satisfaction.send(None)
        (xi, di) = inactivity.send(None)
        while di > confidence_width or ds > confidence_width or c < 2:
            (s, i, t), c = run(), c + 1
            (xs, ds) = satisfaction.send(s)
            (xi, di) = inactivity.send(i)
            logger.info('Run %d: US = %.2f%% (d = %.3f), '
                        'RI = %.2f%% (d = %.3f), timeout = %.2f',
                        c, xs, ds, xi, di, t)
            if c >= max_runs:
                logger.warning('Max runs (%d) reached, stopping.', max_runs)
                break
        logger.info('All runs done (%d).', c)

    if configuration.get_arg('plot'):
        logger.debug('Storing plots.')
        custom_injector.get(Plot).plot_all()

    logger.debug('Process memory footprint: %.2f MiB',
                 memory_profiler.memory_usage()[0])
