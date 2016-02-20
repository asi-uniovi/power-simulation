"""Base objects for the simulation."""

import abc
import injector

from module import config_key, env_key


@injector.inject(_config=config_key, _env=env_key)
class Base(object, metaclass=abc.ABCMeta):
    """An abstract class with all the basic methods we need across."""

    @property
    def simulating_per_pc(self):
        """Indicates if a config key is defined."""
        return self.config_exists('per_pc_file',
                                  section='inactivity_distribution')

    def config_exists(self, key, section='simulation'):
        """Indicates if a config key is defined."""
        return key in self._config[section]

    def get_config(self, key, section='simulation'):
        """Retrieves a key from the configuration."""
        return self._config.get(section, key)

    def get_config_int(self, key, section='simulation'):
        """Retrieves a key from the configuration (converts to int)."""
        return self._config.getint(section, key)
