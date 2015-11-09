"""Base objects for the simulation."""

import abc
import injector
import six

try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

from module import config_key, env_key


@injector.inject(_config=config_key, _env=env_key)
class Base(six.with_metaclass(abc.ABCMeta, object)):
    """An abstract class with all the basic methods we need across."""

    @lru_cache()
    def get_config(self, key, section='simulation'):
        """Retrieves a key from the configuration."""
        return self._config.get(section, key)

    @lru_cache()
    def get_config_int(self, key, section='simulation'):
        """Retrieves a key from the configuration (converts to int)."""
        return self._config.getint(section, key)

    @lru_cache()
    def get_config_float(self, key, section='simulation'):
        """Retrieves a key from the configuration (converts to float)."""
        return self._config.getfloat(section, key)
