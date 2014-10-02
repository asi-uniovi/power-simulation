"""A very simple simuation of a 1/M/c queuing system."""

import simpy
from activity_distribution import ActivityDistribution
from stats import Stats
from user import User


class Simulation(object):
    """Constructs the system and runs the simulation."""

    def __init__(self, config):
        self._config = config
        self._stats = None
        self._env = None
        self._activity_distribution = ActivityDistribution(
            filename=self.get_config('filename', 'activity_distribution'))

    def run(self):
        """Sets up and starts a new simulation."""
        # Set up the environment.
        self._stats = Stats()
        self._env = simpy.Environment()
        servers = simpy.Resource(self._env, capacity=self.get_config('servers'))

        # Start the simulation.
        self._env.process(User(self._env, self._config, servers))
        self._env.run(until=self.get_config('simulation_time'))

    def get_config(self, key, section='simulation'):
        """Retrieves a key from the configuration."""
        return self._config[section][key]

    def __str__(self):
        if self._stats is None:
            return 'Simulation not ran.'
        return ('Total requests: {}\n'.format(self._stats['REQUESTS'])
                + 'Waiting time: {}\n'.format(self._stats['WAITING_TIME'])
                + 'Served requests: {}'.format(self._stats['SERVED_REQUESTS']))
