"""A very simple simuation of a 1/M/c queuing system."""

import logging
import simpy
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
        self._stats = Stats()
        self._env = None

    def _create_user(self):
        computer = Computer(self._config, self._env)
        user = User(self._config, self._env, computer)
        os = SimpleTimeoutOS(self._config, self._env, computer)
        self._env.process(user.run())

    def run(self):
        """Sets up and starts a new simulation."""
        self._stats.clear()
        self._env = simpy.Environment()

        for i in range(100):
            self._create_user()

        logger.info('Simulation starting')
        self._env.run(until=self.get_config_int('simulation_time'))
        self.__log_results()

    def __log_results(self):
        if self._env is None:
            logger.warning('Simulation not ran')
            return
        total_requests = self._stats['REQUESTS']
        served_requests = self._stats['SERVED_REQUESTS']
        logger.info('Simulation ended at %d s', self._env.now)
        logger.info('Total requests: %d', total_requests)
        logger.info('Total served requests: %d (%.2f%%)',
                    served_requests, served_requests / total_requests * 100)
        logger.info('Avg. waiting time: %.3f s',
                    self._stats['WAITING_TIME'] / served_requests)
        logger.info('Avg. serving time: %.3f s',
                    self._stats['SERVING_TIME'] / served_requests)
        logger.info('Avg. inactivity time: %.3f s',
                    self._stats['INACTIVITY_TIME'] / served_requests)
