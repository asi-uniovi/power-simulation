"""A very simple simuation of a 1/M/c queuing system."""

import injector
import logging

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

    @property
    def simulation_time(self):
        """Gets the simulation time from the config."""
        return self.get_config_int('simulation_time')

    @property
    def servers(self):
        """Gets the server count from the config."""
        return self.get_config_int('servers')

    def run(self):
        """Sets up and starts a new simulation."""
        servers = self.get_config_int('servers')
        logger.info('Simulating %d users (%d s)', servers, self.simulation_time)
        self._env.process(self.__monitor_time())
        for _ in range(servers):
            self._env.process(CustomInjector(Binder()).get(User).run())
        logger.info('Simulation starting')
        self._env.run(until=self.simulation_time)
        logger.info('Simulation ended at %d s', self._env.now)
        self.__log_results()

    def __log_results(self):
        """Prints the final results of the simulation run."""
        at = self._stats.sum_histograms('ACTIVITY_TIME') / self.servers
        ust = self._stats.sum_histograms('USER_SHUTDOWN_TIME') / self.servers
        it = self._stats.sum_histograms('INACTIVITY_TIME') / self.servers
        ast = self._stats.sum_histograms('AUTO_SHUTDOWN_TIME') / self.servers
        idt = self._stats.sum_histograms('IDLE_TIME') / self.servers

        logger.info('Total = AT + IT + UST (1): %.2f%%',
                    ((ust + at + it) / self.simulation_time - 1) * 100)
        logger.info('Total = AT + IdT + AST + UST (2): %.2f%%',
                    ((ust + at + idt + ast) / self.simulation_time - 1) * 100)
        logger.info('IT = IdT + AST (3): %.2f%%', ((ast + idt) / it - 1)* 100.0)

        self._plot.plot_all('USER_SHUTDOWN_TIME')
        self._plot.plot_all('AUTO_SHUTDOWN_TIME')
        self._plot.plot_all('ACTIVITY_TIME')
        self._plot.plot_all('INACTIVITY_TIME')
        self._plot.plot_all('IDLE_TIME')

    def __monitor_time(self):
        """Indicates how te simulation is progressing."""
        while True:
            logger.info('%.2f%% completed',
                        self._env.now / self.simulation_time * 100.0)
            yield self._env.timeout(self.simulation_time / 10.0)


def runner(config):
    """Bind all and launch the simulation!"""
    custom_injector = CustomInjector(Binder(config))
    custom_injector.get(create_histogram_tables)()
    custom_injector.get(Simulation).run()
