#!/usr/bin/env python3

"""Plots the satisfaction, weighted satisfaction and removed inactivity."""

import argparse
import itertools
import json
import operator
import sys

import matplotlib.pyplot
import matplotlib.ticker
import numpy

# pylint: disable=import-error
from static import user_satisfaction
from static import weighted_user_satisfaction

MAX_TIMEOUT = 1200
STEP = 10


# pylint: disable=invalid-name
def parse_model(traces):
    """Parses the model for a given trace."""
    models = {}
    for t, data in traces.items():
        for d in data:
            models.setdefault(t, []).extend(d['Intervals'])
    return models


# pylint: disable=invalid-name
def parse_trace(trace_file):
    """Parses the trace file to get a list of inactivity intervals."""
    with open(trace_file) as trace:
        trace = json.load(trace)
        trace = [i for i in trace if i['PC'] != '_Total']
        key = operator.itemgetter('PC')
        models = {}
        for pc, trace in itertools.groupby(sorted(trace, key=key), key=key):
            models[pc] = parse_model({t['Type']: t['data'] for t in trace})
        return models


# pylint: disable=invalid-name
def plot_trace(trace):
    """Plots a trace."""
    all_inactivity = numpy.asarray([
        i for pc in trace.values() for i in pc['InactivityIntervals']])
    total_inactivity = numpy.sum(all_inactivity)
    vit = []
    us = []
    wus = []
    ri = []
    x = 0.0

    while x <= MAX_TIMEOUT:
        vit.append(x)
        us.append(sum(user_satisfaction(all_inactivity, x))
                  / len(all_inactivity) * 100)
        wus.append(sum(weighted_user_satisfaction(all_inactivity, x, 1800))
                   / len(all_inactivity) * 100)
        ri.append(sum(i - x for i in all_inactivity if i > x)
                  / total_inactivity * 100)
        x += STEP

    matplotlib.pyplot.style.use('bmh')
    _, ax = matplotlib.pyplot.subplots(1, 1)
    vit = numpy.asarray(vit) / 60
    ax.plot(vit, us, label='User Satisfaction (%)',
            linewidth=2, color='green', marker='s', markersize=3)
    ax.plot(vit, wus, label='Weighted User Satisfaction (%)',
            linewidth=2, color='blue', marker='h', markersize=4)
    ax.plot(vit, ri, label='Removed Inactivity (%)',
            linewidth=2, color='red', marker='o', markersize=4)
    ax.set_xlim([1.0, MAX_TIMEOUT / 60])
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
    ax.set_ylim([0.0, 100.0])
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(10))
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(2))
    matplotlib.pyplot.xlabel(r'Timeout value, $V_{IT}$ (minutes)')
    ax.legend(loc='best', frameon=False)
    ax.grid(True, which='both')
    matplotlib.pyplot.savefig('figure.png')


def main():
    """Just parses arguments and moves forward."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace',
                        dest='trace_file',
                        help='path to the trace file to analyse')
    plot_trace(parse_trace(parser.parse_args().trace_file))


if __name__ == '__main__':
    sys.exit(main())
