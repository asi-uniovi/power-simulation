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
import random
import scipy.stats
import sqlite3
import time
import typing
from simulation.activity_distribution import DistributionFactory
from simulation.configuration import Configuration
from simulation.histogram import create_histogram_tables
from simulation.module import Module
from simulation.plot import Plot
from simulation.static import config_logging, profile, timed, WEEK
from simulation.stats import Stats
from simulation.user import User

logger = logging.getLogger(__name__)


class Simulation(object):
    """Constructs the system and runs the simulation."""

    @injector.inject
    def __init__(self, config: Configuration,
                 distr_factory: DistributionFactory,
                 user_builder: injector.ClassAssistedBuilder[User],
                 plot: Plot, stats: Stats):
        super(Simulation, self).__init__()
        self.__activity_distribution = distr_factory()
        self.__training_distribution = distr_factory(training=True)
        self.__user_builder = user_builder
        self.__plot = plot
        self.__stats = stats
        self.__config = config
        self.target_satisfaction = config.get_config_int('target_satisfaction')

    @property
    def timeout(self) -> float:
        """Average global timeout."""
        return self.__training_distribution.global_idle_timeout()

    @property
    def all_timeouts(self) -> float:
        """Average global timeout."""
        return self.__training_distribution.all_idle_timeouts()

    @property
    def test_timeout(self) -> typing.Tuple[float, float, float]:
        """Average global timeout."""
        return self.__activity_distribution.test_timeout(self.all_timeouts)

    def graph_timeouts(self) -> None:
        """Average global timeout."""
        return self.__training_distribution.graph_results(0, 30*60+1, 30)

    @timed
    def run(self) -> typing.Tuple[float, float]:
        """Sets up and starts a new simulation."""
        self.__config.new_run()
        if self.__config.debug:
            self.__config.env.process(self.__monitor_time())
        for cid in self.__generate_cids():
            self.__config.env.process(self.__user_builder.build(cid=cid).run())
        logger.debug('Simulation starting')
        self.__config.env.run(until=self.__config.simulation_time)
        logger.debug('Simulation ended at %d s', self.__config.env.now)
        self.__stats.flush()
        self.__validate_results()
        results = (self.__stats.user_satisfaction(),
                   self.__stats.removed_inactivity(),
                   self.__stats.optimal_idle_timeout())
        logger.debug('RESULT: Simulated User Satisfaction (US) = %.2f%%', results[0])
        logger.debug('RESULT: Simualted Modified Apdex = %.2f%%', self.__stats.apdex())
        logger.debug('RESULT: Simulated Removed Inactivity (RI) = %.2f', results[1])
        logger.debug('RESULT: Perfect Optimal idle timeout = %.2f%%', results[2])
        logger.debug('Run complete.')
        return results

    def __generate_cids(self) -> typing.List[str]:
        """Generate the computer IDs, so at least all are chosen once."""
        existing_servers = len(self.__activity_distribution.servers)
        sample_size = self.__config.users_num - existing_servers

        cids = random.sample(
            self.__activity_distribution.servers,
            min(self.__config.users_num, existing_servers))

        if sample_size > 0:
            if sample_size <= existing_servers:
                cids.extend(random.sample(
                    self.__activity_distribution.servers, sample_size))
            else:
                cids.extend(random.choices(
                    self.__activity_distribution.servers, k=sample_size))

        return sorted(cids)

    def __validate_results(self) -> None:
        """Performs vaidations on the run results and warns on errors."""
        at = self.__stats.sum_histogram('ACTIVITY_TIME', trim=True)
        ust = self.__stats.sum_histogram('USER_SHUTDOWN_TIME', trim=True)
        ast = self.__stats.sum_histogram('AUTO_SHUTDOWN_TIME', trim=True)
        it = self.__stats.sum_histogram('INACTIVITY_TIME', trim=True)
        val1 = (ust + at + it) / self.__config.simulation_time / (
            self.__config.users_num)

        if 0.99 > val1 > 1.01:
            logger.warning('Validation of total time failed: %.2f', val1)

        if ast > it:
            logger.warning('Validation of auto shut down failed: %.2f > %.2f', ast, it)

    def __monitor_time(self) -> float:
        """Indicates how te simulation is progressing."""
        while True:
            logger.debug(
                '%.2f%% completed',
                self.__config.env.now / self.__config.simulation_time * 100.0)
            yield self.__config.env.timeout(
                self.__config.simulation_time / 10.0)


def confidence_interval(m: float, alpha: float = 0.05):
    """Generator to calculate confidence intervals in a more nicely fashion."""
    x, s, d, i = m, 0, 0, 1
    while True:
        m = yield (x, d)
        i += 1
        s = ((i - 2) / (i - 1) * s) + (1 / i * ((m - x) ** 2))
        x = ((1 - 1 / i) * x) + (1 / i * m)
        d = scipy.stats.t.interval(1 - alpha, i - 1)[1] * math.sqrt(s / i)


@timed
def runner() -> None:
    """Bind all and launch the simulation!"""
    ini = time.process_time()
    custom_injector = injector.Injector([Module])
    configuration = custom_injector.get(Configuration)
    config_logging(configuration)
    create_histogram_tables(custom_injector.get(sqlite3.Connection))
    if configuration.get_arg('debug'):
        numpy.random.seed(0)
    simulator = custom_injector.get(Simulation)
    max_runs = configuration.get_arg('max_runs')
    confidence_width = configuration.get_arg('max_confidence_interval_width')
    run = custom_injector.get(profile)(simulator.run)

    logger.info('Parsing done at second %.2f', time.process_time() - ini)

    logger.info('Simulating %d users during %d s (%.1f week(s)).',
                configuration.users_num, configuration.simulation_time,
                configuration.simulation_time / WEEK(1))
    logger.info('User Satisfaction (US) target is %d%%.',
                simulator.target_satisfaction)
    if simulator.timeout[0] < math.inf:
        logger.info('Average global timeout will be %.2f s '
                    '(median = %.2f s, std = %.2f s)',
                    *simulator.timeout)
        logger.info('A priori WUS = %.2f%% (median = %.2f%%, std = %.2f p.p.), '
                    'US = %.2f%% (median = %.2f%%, std = %.2f p.p.), '
                    'RI = %.2f%%.',
                    *simulator.test_timeout)
        logger.info('A priori analysis at second %.2f', time.process_time() - ini)
        simulator.graph_timeouts()
        logger.info('Graph done %.2f', time.process_time() - ini)
    (s, i, t), c = run(), 1
    logger.info('Run 1: US = %.2f%%, RI = %.2f%%, timeout = %.2f', s, i, t)

    if max_runs == 1 or configuration.get_arg('fleet_generator'):
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

    logger.info('Runs done at second %.2f', time.process_time() - ini)

    if configuration.get_arg('plot'):
        logger.debug('Storing plots.')
        custom_injector.get(Plot).plot_all()

    logger.info('Plotting done at second %.2f', time.process_time() - ini)

    logger.debug('Process memory footprint: %.2f MiB',
                 memory_profiler.memory_usage()[0])

    logger.info('All done at second %.2f', time.process_time() - ini)
