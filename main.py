#!/usr/bin/env python

"""Main runner of the simulation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import argparse
import logging
import os
import signal
import sys
import warnings

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from simulation import runner


def sigterm_handler(signal, frame):
    import pdb
    pdb.set_trace()


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
    return parser.parse_args()


def parse_config(config_file):
    """Get the config file as a dict of dicts."""
    if not os.path.isfile(config_file):
        raise ValueError('The configuration file does not exist')

    config = configparser.ConfigParser()
    config.read(config_file)
    return config


def configure():
    """Sets the basic configuration and dependency injections."""
    args = parse_arguments()
    config_logging(args.debug)
    return parse_config(args.config_file)


def main():
    """Just starts the simulation."""
    try:
        runner(configure())
    except:
        logging.exception('Unexpected exception')
        return 1


if __name__ == '__main__':
    warnings.simplefilter('error')
    signal.signal(signal.SIGTERM, sigterm_handler)
    sys.exit(main())
