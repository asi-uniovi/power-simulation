#!/usr/bin/env python

"""Main runner of the simulation."""

from __future__ import division
from __future__ import print_function

import argparse
import logging
import os
import sys
import configparser
from simulation import Simulation


def config_logging(debug):
    """Sets logging basic config"""
    logging.basicConfig(
        format='%(asctime)s %(levelname)s(%(name)s): %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S',
        level=logging.DEBUG if debug else logging.INFO)


def parse_arguments():
    """Get the arguments in a standard way."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="show debug information",
                        action="store_true")
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
        config_logging(args.debug)
        config = parse_config(args.config_file)
        Simulation(config).run()
    except:
        logging.exception('Unexpected exception')
        return 1


if __name__ == '__main__':
    sys.exit(main())
