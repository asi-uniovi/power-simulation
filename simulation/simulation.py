"""A very simple simuation of several 1/M/c queuing systems."""

import logging
import math
import sqlite3
import typing
import injector
import memory_profiler
import numpy
import scipy.stats
from simulation.activity_distribution import ActivityDistribution
from simulation.activity_distribution import TrainingDistribution
from simulation.base import Base
from simulation.configuration import Configuration
from simulation.histogram import create_histogram_tables
from simulation.module import Binder, CustomInjector
from simulation.plot import Plot
from simulation.static import config_logging, profile
from simulation.stats import Stats
from simulation.user import User

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Simulation(Base):
    """Constructs the system and runs the simulation."""

    @injector.inject
    # pylint: disable=too-many-arguments
    def __init__(self, activity_distribution: ActivityDistribution,
                 training_distribution: TrainingDistribution,
                 user_builder: injector.AssistedBuilder[User],
                 plot: Plot, stats: Stats):
        super(Simulation, self).__init__()
        self.__activity_distribution = activity_distribution
        self.__training_distribution = training_distribution
        self.__user_builder = user_builder
        self.__plot = plot
        self.__stats = stats
        self.__simulation_time = self.get_config_int('simulation_time')
        self.__target_satisfaction = self.get_config_int('target_satisfaction')
        self.__activity_distribution.intersect(self.__training_distribution)

    @property
    def servers(self) -> int:
        """Number of servers being simulated."""
        return len(self.__training_distribution.servers)

    @property
    def timeout(self) -> float:
        """Average global timeout."""
        return self.__training_distribution.global_idle_timeout()

    def run(self) -> typing.Tuple[float, float]:
        """Sets up and starts a new simulation."""
        self._config.reset()
        self.__stats.reset()
        logger.debug('Simulating %d users (%d s)',
                     self.servers, self.__simulation_time)
        logger.debug(
            'Target user satisfaction %d%%', self.__target_satisfaction)
        if self._config.get_arg('debug'):
            self._config.env.process(self.__monitor_time())
        for cid in self.__training_distribution.servers:
            if cid in self.__activity_distribution.servers:
                self._config.env.process(
                    self.__user_builder.build(cid=cid).run())
        logger.debug('Simulation starting')
        self._config.env.run(until=self.__simulation_time)
        logger.debug('Simulation ended at %d s', self._config.env.now)
        if self._config.get_arg('debug'):
            self.__validate_results()
        results = (self.__stats.user_satisfaction(),
                   self.__stats.removed_inactivity())
        logger.debug('RESULT: User Satisfaction (US) = %.2f%%', results[0])
        logger.debug('RESULT: Removed Inactivity (RI) = %.2f%%', results[1])
        if self.get_arg('plot'):
            self.__plot_results()
        logger.debug('Run complete.')
        return results

    def __plot_results(self) -> None:
        """Plots the results."""
        logger.debug('Storing plots.')
        self.__plot.plot_all('USER_SHUTDOWN_TIME')
        self.__plot.plot_all('AUTO_SHUTDOWN_TIME')
        self.__plot.plot_all('ACTIVITY_TIME')
        self.__plot.plot_all('INACTIVITY_TIME')
        self.__plot.plot_all('IDLE_TIME')

    def __validate_results(self) -> None:
        """Performs vaidations on the simulation results and warns on errors."""
        # pylint: disable=invalid-name,no-member
        at = self.__stats.sum_histogram('ACTIVITY_TIME') / self.servers
        ust = self.__stats.sum_histogram('USER_SHUTDOWN_TIME') / self.servers
        it = self.__stats.sum_histogram('INACTIVITY_TIME') / self.servers
        ast = self.__stats.sum_histogram('AUTO_SHUTDOWN_TIME') / self.servers
        idt = self.__stats.sum_histogram('IDLE_TIME') / self.servers
        val1 = abs((ust + at + it) / self.__simulation_time - 1)
        val2 = abs((ust + at + idt + ast) / self.__simulation_time - 1)
        val3 = abs((ast + idt) / it - 1)

        if val1 > 0.1:
            logger.warning('Validation of total time failed: val1 = %.2f', val1)

        if val2 > 0.1:
            logger.warning('Validation of total time failed: val2 = %.2f', val2)

        if val3 > 0.01:
            logger.warning(
                'Validation of total inactivity failed: val2 = %.2f', val3)

    def __monitor_time(self) -> float:
        """Indicates how te simulation is progressing."""
        while True:
            logger.debug('%.2f%% completed',
                         self._config.env.now / self.__simulation_time * 100.0)
            yield self._config.env.timeout(self.__simulation_time / 10.0)


# pylint: disable=invalid-name
def confidence_interval(m: float, alpha: float=0.05):
    """Generator to calculate confidence intervals in a more nicely fashion."""
    x, s, d, i = m, 0, 0, 1
    while True:
        m = yield (x, d)
        i += 1
        s = ((i - 2) / (i - 1) * s) + (1 / i * ((m - x) ** 2))
        x = ((1 - 1 / i) * x) + (1 / i * m)
        d = scipy.stats.t.interval(1 - alpha, i - 1)[1] * math.sqrt(s / i)


# pylint: disable=invalid-name
def runner() -> None:
    """Bind all and launch the simulation!"""
    custom_injector = CustomInjector(Binder())
    configuration = custom_injector.get(Configuration)
    config_logging(configuration)
    create_histogram_tables(custom_injector.get(sqlite3.Connection))
    if configuration.get_arg('debug'):
        numpy.random.seed(0)  # pylint: disable=no-member
    simulator = custom_injector.get(Simulation)
    max_runs = configuration.get_arg('max_runs')
    confidence_width = configuration.get_arg('max_confidence_interval_width')
    run = custom_injector.get(profile)(simulator.run)

    logger.info('Going to simulate %d users', simulator.servers)
    logger.info('Average global timeout would be %.2f s', simulator.timeout)
    (s, i), c = run(), 1

    if max_runs == 1:
        logger.warning('Only one run, cannot calculate confidence intervals.')
        logger.info('Run 1: US = %.2f%% (d = Inf), RI = %.2f%% (d = Inf)', s, i)
    else:
        satisfaction, inactivity = confidence_interval(s), confidence_interval(i)
        (xs, ds), (xi, di) = satisfaction.send(None), inactivity.send(None)
        while di > confidence_width or ds > confidence_width or c < 2:
            (s, i), c = run(), c + 1
            (xs, ds), (xi, di) = satisfaction.send(s), inactivity.send(i)
            logger.info('Run %d: US = %.2f%% (d = %.4f), RI = %.2f%% (d = %.4f)',
                        c, xs, ds, xi, di)
            if c > max_runs:
                logger.warning('Finishing simulation runs due to inconvergence.')
                break
        logger.info('All runs done (%d).', c)

    logger.info(
        'Process memory footprint: %.2f MiB', memory_profiler.memory_usage()[0])
