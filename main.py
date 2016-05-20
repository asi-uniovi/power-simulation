#!/usr/bin/env python3

"""Main runner of the simulation."""

import logging
import sys
import warnings

from configuration import Configuration
from simulation import runner


def main(_):
    """Just starts the simulation."""
    try:
        runner()
    except:  # pylint: disable=bare-except
        logging.exception('Unexpected exception')
        return 1


if __name__ == '__main__':
    warnings.simplefilter('error')
    sys.exit(main(Configuration()))
