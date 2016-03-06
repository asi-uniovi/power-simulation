"""A very simple simuation of a 1/M/c queuing system."""

import logging

import injector

from activity_distribution import ActivityDistribution
from base import Base
from histogram import create_histogram_tables
from module import Binder, CustomInjector
from plot import Plot
from stats import Stats
from user import User

logger = logging.getLogger(__name__)


@injector.inject(_activity_distribution=ActivityDistribution,
                 _plot=Plot,
                 _stats=Stats)
class Simulation(Base):
    """Constructs the system and runs the simulation."""

    def __init__(self):
        super(Simulation, self).__init__()
        self.__simulation_time = self.get_config_int('simulation_time')
        self.__target_satisfaction = self.get_config_int('target_satisfaction')

    @property
    def servers(self):
        """Number of servers being simulated."""
        return len(self._activity_distribution.servers)

    def run(self):
        """Sets up and starts a new simulation."""
        logger.info('Simulating %d users (%d s)',
                    self.servers, self.__simulation_time)
        logger.info('Target user satisfaction %d%%', self.__target_satisfaction)
        logger.info('Average global timeout would be %.2f s',
                    self._activity_distribution.global_idle_timeout())
        self._env.process(self.__monitor_time())
        for _ in range(self.servers):
            self._env.process(CustomInjector(Binder()).get(User).run())
        logger.info('Simulation starting')
        self._env.run(until=self.__simulation_time)
        logger.info('Simulation ended at %d s', self._env.now)
        self.__validate_results()
        self.__log_results()
        logger.info('Run complete.')

    def __log_results(self):
        """Prints the final results of the simulation run."""
        logger.info('User Satisfaction (US) = %.2f%%',
                    self._stats.user_satisfaction())
        logger.info('Removed Inactivity (RI) = %.2f%%',
                    self._stats.removed_inactivity())
        logger.info('Storing plots.')
        self._plot.plot_all('USER_SHUTDOWN_TIME')
        self._plot.plot_all('AUTO_SHUTDOWN_TIME')
        self._plot.plot_all('ACTIVITY_TIME')
        self._plot.plot_all('INACTIVITY_TIME')
        self._plot.plot_all('IDLE_TIME')

    def __validate_results(self):
        """Performs vaidations on the simulation results and warns on errors."""
        at = self._stats.sum_histogram('ACTIVITY_TIME') / self.servers
        ust = self._stats.sum_histogram('USER_SHUTDOWN_TIME') / self.servers
        it = self._stats.sum_histogram('INACTIVITY_TIME') / self.servers
        ast = self._stats.sum_histogram('AUTO_SHUTDOWN_TIME') / self.servers
        idt = self._stats.sum_histogram('IDLE_TIME') / self.servers

        if abs((ust + at + it) / self.__simulation_time - 1) > 0.1:
            logger.warning('Validation of total time (1) failed.')

        if abs((ust + at + idt + ast) / self.__simulation_time - 1) > 0.1:
            logger.warning('Validation of total time (2) failed.')

        if abs((ast + idt) / it - 1) > 0.01:
            logger.warning('Validation of total inactivity failed.')

    def __monitor_time(self):
        """Indicates how te simulation is progressing."""
        while True:
            logger.info('%.2f%% completed',
                        self._env.now / self.__simulation_time * 100.0)
            yield self._env.timeout(self.__simulation_time / 10.0)


def runner(config):
    """Bind all and launch the simulation!"""
    custom_injector = CustomInjector(Binder(config))
    custom_injector.get(create_histogram_tables)()
    custom_injector.get(Simulation).run()
