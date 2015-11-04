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


class Simulation(Base):
    """Constructs the system and runs the simulation."""

    @injector.inject(activity_distribution=ActivityDistribution, plot=Plot,
                     stats=Stats)
    def __init__(self, activity_distribution, plot, stats):
        super(Simulation, self).__init__()
        self._activity_distribution = activity_distribution
        self._plot = plot
        self._stats = stats

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
        total_requests = self._stats.get_statistics('REQUESTS')['count']
        served_requests = self._stats.get_statistics('SERVED_REQUESTS')['count']
        waiting_time = self._stats.get_statistics('WAITING_TIME')['sum']
        serving_time = self._stats.get_statistics('SERVING_TIME')['sum']
        inactivity_time = self._stats.get_statistics(
            'INACTIVITY_TIME_ACCURATE')['mean']
        inactivity_time_monitored = self._stats.get_statistics(
            'INACTIVITY_TIME_MONITORED')['mean']
        try:
            computers_shutdown = self._stats.get_statistics(
                'COMPUTERS_SHUTDOWN')['count']
        except KeyError:
            computers_shutdown = 0
        logger.info('Simulation ended at %d s', self._env.now)
        logger.info('Total requests: %d', total_requests)
        logger.info('Total served requests: %d (%.2f%% completed)',
                    served_requests, served_requests / total_requests * 100)
        logger.info('Avg. waiting time: %.3f s',
                    waiting_time / served_requests)
        logger.info('Avg. serving time: %.3f s',
                    serving_time / served_requests)
        # pylint: disable=no-member
        logger.info('Avg. inactivity time: %.3f s', inactivity_time)
        logger.info('Avg. inactivity time (monitored): %.3f s',
                    inactivity_time_monitored)
        logger.info('Shutdown events: %d', computers_shutdown)
        self._plot.plot_activity_means_and_medians()
        self._plot.plot_inactivity_means_and_medians()
        self._plot.plot_inactivity_counts_and_shutdowns()
        self._plot.plot_generic_histogram('SHUTDOWN_INTERVAL')

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
