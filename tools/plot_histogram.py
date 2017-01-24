#!/usr/bin/env python3

"""Plots the histogram of one of the trace keys."""

import argparse
import sys
import matplotlib.mlab
import matplotlib.pyplot
import numpy
import scipy.stats
from tools.parse_trace import parse_trace


def plot_histogram(trace, key, nbins, distribution_to_fit):
    """Plots a trace."""
    all_items = numpy.asarray([
        i for pc in trace.values() for i in pc[key]])
    shape, loc, scale = getattr(scipy.stats, distribution_to_fit).fit(all_items)
    fit = getattr(scipy.stats, distribution_to_fit)(shape, loc, scale)

    matplotlib.pyplot.style.use('bmh')
    _, axis = matplotlib.pyplot.subplots(1, 1)

    _, bins, _ = axis.hist(all_items, nbins, normed=1)
    axis.plot(bins, fit.pdf(bins), 'r--', linewidth=1)

    matplotlib.pyplot.xlabel('Histogram for key "%s"' % key)
    matplotlib.pyplot.ylabel('Probability')
    axis.grid(True, which='both')
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
                        dest='nbins', type=int, default=100,
                        help='number of histogram hins to have')
    parser.add_argument('--distribution_to_fit',
                        dest='distribution_to_fit', default='norm',
                        help='which distribution to fit')
    args = parser.parse_args()
    try:
        plot_histogram(parse_trace(args.trace_file), args.key, args.nbins,
                       args.distribution_to_fit)
    except KeyError:
        print('Invalid key: %s' % args.key)
        return 1


if __name__ == '__main__':
    sys.exit(main())
