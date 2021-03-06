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
import matplotlib.mlab
import matplotlib.pyplot
import numpy
import powerlaw
from simulation.static import REVERSE_DAYS
from tools.parse_trace import parse_trace


def plot_distribution(trace_file, key, day, hours):
    """Plots a trace."""
    matplotlib.pyplot.style.use('bmh')
    figure, axes = matplotlib.pyplot.subplots(nrows=len(hours))
    if len(hours) == 1:
        axes = [axes]

    for i, hour in enumerate(hours):
        axis = axes[i]
        all_items = numpy.asarray([
            i for pc in parse_trace(
                trace_file, day, hour).values() for i in pc[key]])

        fit = powerlaw.Fit(all_items, discrete=True, xmax=None)
        fit.plot_pdf(ax=axis, color='r', linewidth=3, label='Empirical')
        fit.power_law.plot_pdf(
            ax=axis, color='g', linestyle='--', linewidth=1,
            label='powerlaw fit')
        fit.lognormal.plot_pdf(
            ax=axis, color='b', linestyle='--', linewidth=1,
            label='lognormal fit')

        axis.set_xlim(50, 10**5)
        axis.grid(True, which='major')
        axis.set_title('%s, %d:00' % (REVERSE_DAYS[day], hour))

    figure.legend(handles=axis.lines, ncol=len(axis.lines), loc='lower center')
    figure.text(0.5, 0.04, 'Interval duration (s)', ha='center')
    figure.text(0.04, 0.5, 'Probability', va='center', rotation='vertical')
    figure.set_size_inches(6, 2 * len(hours))
    figure.tight_layout(rect=[0.05, 0.05, 1.0, 1.0])
    matplotlib.pyplot.savefig('powerlaw.png')


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
    parser.add_argument('--hours', required=True, nargs='+',
                        dest='hours', type=int,
                        help='hours of the week to analyse (0-23)')
    args = parser.parse_args()
    try:
        plot_distribution(args.trace_file, args.key, args.day, args.hours)
    except KeyError:
        print('Invalid key: %s' % args.key)


if __name__ == '__main__':
    sys.exit(main())
