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

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@injector.inject(_activity_distribution=ActivityDistribution,
                 _plot=Plot,
                 _stats=Stats)
class Simulation(Base):
    """Constructs the system and runs the simulation."""

    @property
    def simulation_time(self):
        """Gets the simulation time from the config."""
        return self.get_config_int('simulation_time')

    def run(self):
        """Sets up and starts a new simulation."""
        servers = self.get_config_int('servers')
        logger.info('Simulating %d users (%d s)', servers, self.simulation_time)
        self._env.process(self.__monitor_time())
        for _ in range(servers):
            self._env.process(CustomInjector(Binder()).get(User).run())
        logger.info('Simulation starting')
        self._env.run(until=self.simulation_time)
        self.__log_results()

    def __log_results(self):
        """Prints the final results of the simulation run."""
        logger.info('Simulation ended at %d s', self._env.now)
        self._plot.plot_hourly_histogram_quantiles('INACTIVITY_TIME_ACCURATE')
        self._plot.plot_hourly_histogram_quantiles('SHUTDOWN_TIME')
        self._plot.plot_hourly_histogram_quantiles('ACTIVITY_TIME')
        self._plot.plot_mean_medians_comparison('INACTIVITY_TIME_ACCURATE')
        self._plot.plot_mean_medians_comparison('SHUTDOWN_TIME')
        self._plot.plot_mean_medians_comparison('ACTIVITY_TIME')
        self._plot.plot_hourly_histogram_count('INACTIVITY_TIME_ACCURATE')
        self._plot.plot_hourly_histogram_count('SHUTDOWN_TIME')
        self._plot.plot_hourly_histogram_count('ACTIVITY_TIME')

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
