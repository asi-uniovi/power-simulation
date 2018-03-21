#!/usr/bin/env python3
#
# Copyright 2018 Google Inc.
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

"""Plots the distribution (PDF, CDF, etc.) of a given day and hour."""

import argparse
import sys
import matplotlib
matplotlib.use('Agg')
# pylint: disable=wrong-import-position
import matplotlib.mlab
import matplotlib.pyplot
import numpy
import powerlaw
from simulation.static import REVERSE_DAYS
from tools.parse_trace import parse_trace


def plot_distribution(trace, key, day, hour):
    """Plots a trace."""
    all_items = numpy.asarray([
        i for pc in trace.values() for i in pc[key]])

    matplotlib.pyplot.style.use('bmh')
    figure, axis = matplotlib.pyplot.subplots(1, 1)

    powerlaw.plot_pdf(all_items, ax=axis,
                      label='%s (%s, %d:00)' % (key, REVERSE_DAYS[day], hour))

    axis.set_xlim(10, 10**6)
    axis.grid(True, which='both')
    axis.legend(loc='best', frameon=False)
    figure.set_size_inches(6, 3)
    figure.set_tight_layout(True)
    matplotlib.pyplot.xlabel('Interval duration (s)')
    matplotlib.pyplot.ylabel('Probability')
    matplotlib.pyplot.savefig('powerlaw-%s-%s-%d.png' % (
        key, REVERSE_DAYS[day], hour))


def main():
    """Just parses arguments and moves forward."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', required=True,
                        dest='trace_file',
                        help='path to the trace file to analyse')
    parser.add_argument('--key', required=True,
                        dest='key',
                        help='key in the trace to process')
    parser.add_argument('--day', required=True,
                        dest='day', type=int,
                        help='day of the week to analyse (0=Sun)')
    parser.add_argument('--hour', required=True,
                        dest='hour', type=int,
                        help='hour of the week to analyse (0-23)')
    args = parser.parse_args()
    try:
        trace = parse_trace(args.trace_file, args.day, args.hour)
        plot_distribution(trace, args.key, args.day, args.hour)
    except KeyError:

        print('Invalid key: %s' % args.key)
        return 1


if __name__ == '__main__':
    sys.exit(main())
