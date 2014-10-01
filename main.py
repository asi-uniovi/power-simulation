#!/usr/bin/env python3

"""Main runner of the simulation."""

import argparse
import sys
import configparser
from simulation import Simulation


def parse_arguments():
    """Get the arguments in a standard way."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config_file', default='config.ini')
    return parser.parse_args()


def parse_config(config_file):
    """Get the config file as a dict of dicts."""
    config = configparser.ConfigParser()
    config.read(config_file)
    return config


def main():
    """Just starts the simulation."""
    args = parse_arguments()
    config = parse_config(args.config_file)
    Simulation(config).run()


if __name__ == '__main__':
    sys.exit(main())
