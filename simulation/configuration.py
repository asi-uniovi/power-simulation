"""Global configuration for the simulation."""

import argparse
import configparser
import os
import injector
import simpy


# pylint: disable=invalid-name
def positive_int(x: str) -> int:
    """Parse ints that are positive numbers."""
    x = int(x)
    if x < 0:
        raise argparse.ArgumentTypeError('%r should be positive (int)' % x)
    return x


# pylint: disable=invalid-name
def positive_float(x: str) -> float:
    """Parse floats that are positive numbers."""
    x = float(x)
    if x < 0.0:
        raise argparse.ArgumentTypeError('%r should be positive (float)' % x)
    return x


@injector.singleton
class Configuration:
    """Wrapper for the command line arguments and other global configs."""

    def __init__(self):
        super(Configuration, self).__init__()
        self.__env = simpy.Environment()
        self.__parse_args()
        self.__parse_config()

    @property
    def env(self) -> simpy.Environment:
        """Current simulation environment."""
        return self.__env

    def reset(self) -> None:
        """Resets the configuration to be able to start a new run."""
        self.__env = simpy.Environment()

    def get_arg(self, key: str) -> str:
        """Forwards the get action to the args container."""
        return getattr(self.__args, key)

    def get_config(self, key: str, section: str='simulation') -> str:
        """Forwards the get action to the config container."""
        return self.__config.get(section, key)

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
                            help='generate distributions grouped by PC')
        parser.add_argument('--per_hour',
                            action='store_true',
                            help='generate distributions grouped by hour')
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
        self.__args = parser.parse_args()
