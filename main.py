#!/usr/bin/env python3

"""Main runner of the simulation."""

import argparse
import logging
import os
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
    if not os.path.isfile(config_file):
        raise ValueError('The configuration file does not exist')

    config = configparser.ConfigParser()
    config.read(config_file)
    return config


def main():
    """Just starts the simulation."""
    try:
        args = parse_arguments()
        config = parse_config(args.config_file)
        return Simulation(config).run()
    except ValueError as value_error:
        logging.error(value_error)
        return 2
    except RuntimeError as runtime_error:
        logging.critical(runtime_error)
        return 1
    except:
        logging.exception('Unexpected exception')
        return 1


if __name__ == '__main__':
    sys.exit(main())
