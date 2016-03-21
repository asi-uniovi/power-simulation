#!/usr/bin/env python3 -B

"""Main runner of the simulation."""

import argparse
import configparser
import cProfile
import logging
import os
import sys
import warnings

from simulation import runner


def config_logging(debug):
    """Sets logging basic config"""
    logging.basicConfig(
        format='%(asctime)s %(levelname)s(%(name)s): %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S',
        level=logging.DEBUG if debug else logging.INFO)
    logging.captureWarnings(True)


def parse_arguments():
    """Get the arguments in a standard way."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="show debug information",
                        action="store_true")
    parser.add_argument('--config', dest='config_file', default='config.ini')
    parser.add_argument('--noplot', dest='plot', action='store_false')
    parser.add_argument('--trace', dest='trace', action='store_true')
    return parser.parse_args()


def parse_config(args):
    """Get the config file as a dict of dicts."""
    if not os.path.isfile(args.config_file):
        raise ValueError('The configuration file does not exist')

    config = configparser.ConfigParser()
    config.read(args.config_file)
    return config

def main():
    """Just starts the simulation."""
    try:
        args = parse_arguments()
        config_logging(args.debug)
        if args.trace:
            pr = cProfile.Profile()
            pr.enable()
        runner(parse_config(args), plot=args.plot)
        if args.trace:
            pr.create_stats()
            pr.dump_stats('trace')
    except:
        logging.exception('Unexpected exception')
        return 1


if __name__ == '__main__':
    warnings.simplefilter('error')
    sys.exit(main())
