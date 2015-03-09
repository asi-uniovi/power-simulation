"""A very simple simuation of a 1/M/c queuing system."""

import logging
import numpy
import simpy
from activity_distribution import ActivityDistribution
from base import Base
from operating_system import SimpleTimeoutOS
from computer import Computer
from stats import Stats
from user import User

logger = logging.getLogger(__name__)


class Simulation(Base):
    """Constructs the system and runs the simulation."""

    def __init__(self, config):
        super(Simulation, self).__init__(config)
        self._env = None
        self._stats = None
        self._monitoring_interval = None

    def _create_user(self, activity_distribution):
        """Creates a user and the dependent simulation objects (computers)."""
        computer = Computer(self._config, self._env)
        user = User(self._config, self._env, computer, activity_distribution)
        SimpleTimeoutOS(self._config, self._env, computer)
        self._env.process(user.run())

    def run(self):
        """Sets up and starts a new simulation."""
        simulation_time = self.get_config_int('simulation_time')
        self._monitoring_interval = simulation_time / 10.0
        self._env = simpy.Environment()
        self._stats = Stats(self._config, self._env)
        self._env.process(self.__monitor_time())

        activity_distribution = (
            ActivityDistribution.load_activity_distribution(self._config,
                                                            self._env))
        servers = self.get_config_int('servers')
        logger.info('Simulating %d users', servers)
        for _ in range(servers):
            self._create_user(activity_distribution)

        logger.info('Simulation starting')
        self._env.run(until=simulation_time)
        self.__log_results()

    def __log_results(self):
        """Prints the final results of the simulation run."""
        if self._env is None:
            logger.warning('Simulation not ran')
            return
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

    def __monitor_time(self):
        while True:
            print('{} seconds completed'.format(self._env.now))
            yield self._env.timeout(self._monitoring_interval)
