"""Base objects for the simulation."""

import abc


class Base(metaclass=abc.ABCMeta):
    """An abstract class with all the basic methods we need across."""

    def __init__(self, config):
        self._config = config
        self._env = None

    def get_config(self, key, section='simulation'):
        """Retrieves a key from the configuration."""
        return self._config[section][key]

    def get_config_int(self, key, section='simulation'):
        """Retrieves a key from the configuration (converts to int)."""
        return self._config.getint(section, key)
