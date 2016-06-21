"""Base objects for the simulation."""

import abc
import injector

from configuration import Configuration


@injector.inject(_config=Configuration)
class Base(object, metaclass=abc.ABCMeta):
    """An abstract class with all the basic methods we need across."""

    def get_config(self, key, section='simulation'):
        """Retrieves a key from the configuration."""
        # pylint: disable=no-member
        return self._config.get_config(key, section)

    def get_config_int(self, key, section='simulation'):
        """Retrieves a key from the configuration (converts to int)."""
        return int(self.get_config(key, section))

    def get_config_float(self, key, section='simulation'):
        """Retrieves a key from the configuration (converts to float)."""
        return float(self.get_config(key, section))

    def get_arg(self, key):
        """Gets the value of a command line argument."""
        return self._config.get_arg(key)  # pylint: disable=no-member
