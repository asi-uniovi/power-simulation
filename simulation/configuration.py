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

"""Global configuration for the simulation."""

import argparse
import configparser
import os
import injector
import simpy


def positive_int(x: str) -> int:
    """Parse ints that are positive numbers."""
    x = int(x)
    if x < 0:
        raise argparse.ArgumentTypeError('%r should be positive (int)' % x)
    return x


def positive_float(x: str) -> float:
    """Parse floats that are positive numbers."""
    x = float(x)
    if x < 0.0:
        raise argparse.ArgumentTypeError('%r should be positive (float)' % x)
    return x


@injector.singleton
class Configuration(object):
    """Wrapper for the command line arguments and other global configs."""

    def __init__(self):
        super(Configuration, self).__init__()
        self.__parse_args()
        self.__parse_config()
        self.__runs = 0
        self.__env = None

    @property
    def runs(self) -> int:
        """Indicates the number of runs."""
        return self.__runs

    @property
    def env(self) -> simpy.Environment:
        """Current SimPy environment in use."""
        return self.__env

    def new_run(self) -> None:
        """Start a new simulation run."""
        self.__runs += 1
        self.__env = simpy.Environment()

    @property
    def training_time(self) -> int:
        """Indicates the simulation duration."""
        return self.get_config_int('duration', section='training_distribution')

    @property
    def debug(self) -> bool:
        """Indicates if this is a debug run."""
        return bool(self.get_arg('debug'))

    @property
    def users_num(self) -> int:
        """Number of users being simulated."""
        return self.get_arg('users') or self.get_config_int('users')

    @property
    def simulation_time(self) -> int:
        """Indicates the simulation duration."""
        return self.get_arg('simulation_time') or self.get_config_int(
            'duration', section='activity_distribution')

    @property
    def simulation_weeks(self) -> float:
        """Indicates the simulation duration in weeks."""
        return self.simulation_time / 604800

    @property
    def training_weeks(self) -> float:
        """Indicates the simulation duration in weeks."""
        return self.training_time / 604800

    def get_arg(self, key: str) -> str:
        """Forwards the get action to the args container."""
        return getattr(self.__args, key)

    def get_config(self, key: str, section: str = 'simulation') -> str:
        """Forwards the get action to the config container."""
        return self.__config.get(section, key)

    def get_config_int(self, key: str, section: str = 'simulation') -> int:
        """Forwards the get action to the config container."""
        return self.__config.getint(section, key)

    def get_config_float(self, key: str, section: str = 'simulation') -> float:
        """Forwards the get action to the config container."""
        return self.__config.getfloat(section, key)

    def __parse_config(self) -> None:
        """Get the config file as a dict of dicts."""
        if not os.path.isfile(self.__args.config_file):
            raise ValueError('The configuration file does not exist: %s'
                             % self.__args.config_file)
        self.__config = configparser.ConfigParser()
        self.__config.read(self.__args.config_file)

    def __parse_args(self) -> None:
        """Parses the configuration from the command line args."""
        parser = argparse.ArgumentParser()
        parser.add_argument('-d', '--debug',
                            action='store_true',
                            help='show detailed debug information')
        parser.add_argument('--config',
                            dest='config_file', default='config.ini',
                            help='path to the config file of the simulation')
        parser.add_argument('--noplot',
                            dest='plot', action='store_false',
                            help='disable the plot generation (takes time)')
        parser.add_argument('--trace',
                            action='store_true',
                            help='generate a profiling trace')
        parser.add_argument('--per_pc',
                            action='store_true',
                            help='do not merge by PC')
        parser.add_argument('--per_hour',
                            action='store_true',
                            help='do not merge by hour')
        parser.add_argument('--max_runs',
                            type=positive_int, default=100,
                            help='do not run the simulation more than this')
        parser.add_argument('--max_confidence_interval_width',
                            type=positive_float, default=0.5,
                            help=('run simulations until the confidence '
                                  'intervals are narrower than this'))
        parser.add_argument('--fleet_generator',
                            action='store_true',
                            help=('Generate random fleets instead of using '
                                  'training data from usage logs.'))
        parser.add_argument('--disable_auto_shutdown',
                            action='store_true',
                            help=('Disable the control that turns computers '
                                  'off automatically.'))
        parser.add_argument('--simulation_time',
                            type=positive_int,
                            help='Override simulation time from the config.')
        parser.add_argument('--users',
                            type=positive_int,
                            help='Override number of users from the config.')
        self.__args = parser.parse_args()
