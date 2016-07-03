"""A very simple simuation of several 1/M/c queuing systems."""

import logging
import math

import injector
import scipy.stats

from activity_distribution import ActivityDistribution
from activity_distribution import TrainingDistribution
from base import Base
from histogram import create_histogram_tables
from module import Binder, CustomInjector
from plot import Plot
from static import config_logging, profile, MAX_CONFIDENCE_WIDTH, MAX_RUNS
from stats import Stats
from user import User

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@injector.inject(_activity_distribution=ActivityDistribution,
                 _training_distribution=TrainingDistribution,
                 _user_builder=injector.AssistedBuilder(cls=User),
                 _plot=Plot,
                 _stats=Stats)
# pylint: disable=no-member
class Simulation(Base):
    """Constructs the system and runs the simulation."""

    def __init__(self):
        super(Simulation, self).__init__()
        self.__simulation_time = self.get_config_int('simulation_time')
        self.__target_satisfaction = self.get_config_int('target_satisfaction')
        self._activity_distribution.remove_servers(
            self._training_distribution.empty_servers)
        self._training_distribution.remove_servers(
            self._activity_distribution.empty_servers)

    @property
    def servers(self):
        """Number of servers being simulated."""
        return len(self._training_distribution.servers)

    @property
    def timeout(self):
        """Average global timeout."""
        return self._training_distribution.global_idle_timeout()

    def run(self):
        """Sets up and starts a new simulation."""
        self._config.reset()
        self._stats.reset()
        logger.debug('Simulating %d users (%d s)',
                     self.servers, self.__simulation_time)
        logger.debug('Target user satisfaction %d%%', self.__target_satisfaction)
        if self._config.get_arg('debug'):
            self._config.env.process(self.__monitor_time())
        for cid in self._training_distribution.servers:
            self._config.env.process(self._user_builder.build(cid=cid).run())
        logger.debug('Simulation starting')
        self._config.env.run(until=self.__simulation_time)
        logger.debug('Simulation ended at %d s', self._config.env.now)
        if self._config.get_arg('debug'):
            self.__validate_results()
        results = (self._stats.user_satisfaction(),
                   self._stats.removed_inactivity())
        logger.debug('RESULT: User Satisfaction (US) = %.2f%%', results[0])
        logger.debug('RESULT: Removed Inactivity (RI) = %.2f%%', results[1])
        if self.get_arg('plot'):
            self.__plot_results()
        logger.debug('Run complete.')
        return results

    def __plot_results(self):
        """Plots the results."""
        logger.debug('Storing plots.')
        self._plot.plot_all('USER_SHUTDOWN_TIME')
        self._plot.plot_all('AUTO_SHUTDOWN_TIME')
        self._plot.plot_all('ACTIVITY_TIME')
        self._plot.plot_all('INACTIVITY_TIME')
        self._plot.plot_all('IDLE_TIME')

    def __validate_results(self):
        """Performs vaidations on the simulation results and warns on errors."""
        # pylint: disable=invalid-name,no-member
        at = self._stats.sum_histogram('ACTIVITY_TIME') / self.servers
        ust = self._stats.sum_histogram('USER_SHUTDOWN_TIME') / self.servers
        it = self._stats.sum_histogram('INACTIVITY_TIME') / self.servers
        ast = self._stats.sum_histogram('AUTO_SHUTDOWN_TIME') / self.servers
        idt = self._stats.sum_histogram('IDLE_TIME') / self.servers
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

    def __monitor_time(self):
        """Indicates how te simulation is progressing."""
        while True:
            logger.debug('%.2f%% completed',
                         self._config.env.now / self.__simulation_time * 100.0)
            yield self._config.env.timeout(self.__simulation_time / 10.0)


# pylint: disable=invalid-name
def confidence_interval(m, alpha=0.05):
    """Generator to calculate confidence intervals in a more nicely fashion."""
    x, s, d, i = m, 0, 0, 1
    while True:
        m = yield (x, d)
        i += 1
        s = ((i - 2) / (i - 1) * s) + (1 / i * ((m - x) ** 2))
        x = ((1 - 1 / i) * x) + (1 / i * m)
        d = scipy.stats.t.interval(1 - alpha, i - 1)[1] * math.sqrt(s / i)


# pylint: disable=invalid-name
def runner():
    """Bind all and launch the simulation!"""
    custom_injector = CustomInjector(Binder())
    custom_injector.get(config_logging)()
    custom_injector.get(create_histogram_tables)()
    simulator = custom_injector.get(Simulation)
    run = custom_injector.get(profile)(simulator.run)

    logger.info('Average global timeout would be %.2f s', simulator.timeout)
    (s, i), c = run(), 1
    satisfaction, inactivity = confidence_interval(s), confidence_interval(i)
    (xs, ds), (xi, di) = satisfaction.send(None), inactivity.send(None)
    while di > MAX_CONFIDENCE_WIDTH or ds > MAX_CONFIDENCE_WIDTH or c < 2:
        (s, i), c = run(), c + 1
        (xs, ds), (xi, di) = satisfaction.send(s), inactivity.send(i)
        logger.info('Run %d: US = %.2f%% (d = %.4f), RI = %.2f%% (d = %.4f)',
                    c, xs, ds, xi, di)
        if c > MAX_RUNS:
            logger.warning('Finishing simulation runs due to inconvergence.')
            break
