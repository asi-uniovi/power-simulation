"""Base objects for the simulation."""

import injector
from simulation.configuration import Configuration


class Base(object):
    """An abstract class with all the basic methods we need across."""

    @injector.inject
    def __init__(self, config: Configuration):
        self._config = config

    def get_config(self, key: str, section: str='simulation') -> str:
        """Retrieves a key from the configuration."""
        return self._config.get_config(key, section)

    def get_config_int(self, key: str, section: str='simulation') -> int:
        """Retrieves a key from the configuration (converts to int)."""
        return int(self.get_config(key, section))

    def get_config_float(self, key: str, section: str='simulation') -> float:
        """Retrieves a key from the configuration (converts to float)."""
        return float(self.get_config(key, section))

    def get_arg(self, key: str) -> str:
        """Gets the value of a command line argument."""
        return self._config.get_arg(key)
