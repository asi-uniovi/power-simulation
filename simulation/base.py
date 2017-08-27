# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Base objects for the simulation."""

import injector
from simulation.configuration import Configuration


class Base(object):
    """An abstract class with all the basic methods we need across."""

    @injector.inject
    def __init__(self, config: Configuration):
        super(Base, self).__init__()
        self._config = config

    @property
    def debug(self):
        """Indicates if this is a debug run."""
        return bool(self.get_arg('debug'))

    def get_config(self, key: str, section: str = 'simulation') -> str:
        """Retrieves a key from the configuration."""
        return self._config.get_config(key, section)

    def get_config_int(self, key: str, section: str = 'simulation') -> int:
        """Retrieves a key from the configuration (converts to int)."""
        return int(self.get_config(key, section))

    def get_config_float(self, key: str, section: str = 'simulation') -> float:
        """Retrieves a key from the configuration (converts to float)."""
        return float(self.get_config(key, section))

    def get_arg(self, key: str) -> str:
        """Gets the value of a command line argument."""
        return self._config.get_arg(key)
