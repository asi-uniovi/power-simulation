"""A very simple simuation of a 1/M/c queuing system."""

import functools
import injector
import logging
import numpy

from activity_distribution import ActivityDistribution
from base import Base
from module import Binder, CustomInjector
from stats import Stats
from user import User

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Simulation(Base):
    """Constructs the system and runs the simulation."""

    @injector.inject(activity_distribution=ActivityDistribution, stats=Stats)
    def __init__(self, activity_distribution, stats):
        super(Simulation, self).__init__()
        self._activity_distribution = activity_distribution
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
        total_requests = self._stats['REQUESTS']
        served_requests = self._stats['SERVED_REQUESTS']
        logger.info('Simulation ended at %d s', self._env.now)
        logger.info('Total requests: %d', total_requests)
        logger.info('Total served requests: %d (%.2f%% completed)',
                    served_requests, served_requests / total_requests * 100)
        logger.info('Avg. waiting time: %.3f s',
                    self._stats['WAITING_TIME'] / served_requests)
        logger.info('Avg. serving time: %.3f s',
                    self._stats['SERVING_TIME'] / served_requests)
        inactivity_intervals = self._stats['INACTIVITY_TIME']
        # pylint: disable=no-member
        logger.info('Avg. inactivity time: %.3f s',
                    numpy.average(inactivity_intervals))
        inactivity_intervals = list(map(  # pylint: disable=bad-builtin
            numpy.average, self._stats['INACTIVITY_TIME_MONITORED'].values()))
        logger.info('Avg. inactivity time (monitored): %.3f s',
                    numpy.average(inactivity_intervals))
        self._stats.dump_histogram_to_file('INACTIVITY_TIME_MONITORED',
                                           'stats-monitored.txt')
        self._stats.dump_histogram_to_file('INACTIVITY_TIME_ACCURATE',
                                           'stats-accurate.txt')
        self._stats.dump_histogram_to_file('COMPUTERS_SHUTDOWN',
                                           'shutdowns.txt')

    def __monitor_time(self):
        """Indicates how te simulation is progressing."""
        while True:
            logger.info('%.2f%% completed',
                        self._env.now / self.simulation_time * 100.0)
            yield self._env.timeout(self.simulation_time / 10.0)


def runner(config):
    CustomInjector(Binder(config)).get(Simulation).run()
