"""A very simple simuation of a 1/M/c queuing system."""

import logging
import simpy
from base import Base
from stats import Stats
from user import User

logger = logging.getLogger(__name__)


class Simulation(Base):
    """Constructs the system and runs the simulation."""

    def __init__(self, config):
        super(Simulation, self).__init__(config)
        self._stats = Stats()
        self._env = None

    def run(self):
        """Sets up and starts a new simulation."""
        logger.info('Simulation starting')
        # Set up the environment.
        self._stats.clear()
        self._env = simpy.Environment()
        servers = simpy.Resource(self._env,
                                 capacity=self.get_config_int('servers'))

        # Start the simulation.
        self._env.process(User(self._config, self._env, servers).run())
        self._env.run(until=self.get_config_int('simulation_time'))
        self.__log_results()

    def __log_results(self):
        if self._env is None:
            logger.warning('Simulation not ran')
            return
        logger.info('Simulation end time %d', self._env.now)
        logger.info('Total requests: %d', self._stats['REQUESTS'])
        logger.info('Total waiting time: %d', self._stats['WAITING_TIME'])
        logger.info('Total served requests: %d', self._stats['SERVED_REQUESTS'])
