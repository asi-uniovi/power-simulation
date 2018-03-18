#!/usr/bin/env python3
#
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

"""Plots the histogram of one of the trace keys."""

import argparse
import logging
import math
import sys
import matplotlib
matplotlib.use('Agg')
# pylint: disable=wrong-import-position
import matplotlib.mlab
import matplotlib.pyplot
import numpy
import scipy.stats
from parse_trace import parse_trace


def plot_histogram(trace, key, nbins, distribution_name, xmax):
    """Plots a trace."""
    all_items = numpy.asarray([
        i for pc in trace.values() for i in pc[key]])

    distribution = getattr(scipy.stats, distribution_name)

    if nbins is None:
        # Use the Freedman-Diaconis estimate.
        nbins = int((numpy.max(all_items) - numpy.min(all_items))
                    / (2 * scipy.stats.iqr(all_items)
                       * math.pow(len(all_items), -1/3)))
        logging.warning('Using %d bins as default for %d samples.',
                        nbins, len(all_items))

    fit = distribution(*distribution.fit(all_items))

    matplotlib.pyplot.style.use('bmh')
    _, axis = matplotlib.pyplot.subplots(1, 1)

    data, bins, _ = axis.hist(all_items, nbins, density=True,
                              label='Histogram for key "%s"' % key)
    axis.plot(bins, fit.pdf(bins), 'r--', linewidth=1,
              label='Best %s fit for key "%s"' % (distribution_name, key))

    axis.set_ylim([0.0, max(data)])
    if xmax is not None:
        axis.set_xlim([0.0, xmax])
    matplotlib.pyplot.xlabel('Interval duration (s)')
    matplotlib.pyplot.ylabel('Probability')
    axis.grid(True, which='both')
    axis.legend(loc='best', frameon=False)
    matplotlib.pyplot.savefig('histogram.png')


def main():
    """Just parses arguments and moves forward."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace',
                        dest='trace_file',
                        help='path to the trace file to analyse')
    parser.add_argument('--key',
                        dest='key',
                        help='key in the trace to process')
    parser.add_argument('--bins',
                        dest='nbins', type=int, default=None,
                        help='number of histogram hins to have')
    parser.add_argument('--distribution_to_fit',
                        dest='distribution_to_fit', default='norm',
                        help='which distribution to fit')
    parser.add_argument('--xmax',
                        dest='xmax', type=int, default=None,
                        help='max for the x axis on the plots')
    args = parser.parse_args()
    try:
        plot_histogram(parse_trace(args.trace_file), args.key, args.nbins,
                       args.distribution_to_fit, args.xmax)
    except KeyError:
        print('Invalid key: %s' % args.key)
        return 1


if __name__ == '__main__':
    sys.exit(main())
