"""A very simple simuation of a 1/M/c queuing system."""

import simpy
from base import Base
from stats import Stats
from user import User


class Simulation(Base):
    """Constructs the system and runs the simulation."""

    def __init__(self, config):
        super(Simulation, self).__init__(config)
        self._stats = Stats()

    def run(self):
        """Sets up and starts a new simulation."""
        # Set up the environment.
        self._stats.clear()
        self._env = simpy.Environment()
        servers = simpy.Resource(self._env,
                                 capacity=self.get_config_int('servers'))

        # Start the simulation.
        self._env.process(User(self._config, self._env, servers).run())
        self._env.run(until=self.get_config_int('simulation_time'))
        print(self)


    def __str__(self):
        if self._stats is None:
            return 'Simulation not ran.'
        return ('End time {}\n'.format(self._env.now)
                +'Total requests: {}\n'.format(self._stats['REQUESTS'])
                + 'Waiting time: {}\n'.format(self._stats['WAITING_TIME'])
                + 'Served requests: {}'.format(self._stats['SERVED_REQUESTS']))
