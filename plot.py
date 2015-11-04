"""Summarizes the stats collected during the simulation in plots."""

import injector
import matplotlib.pyplot as plt
import numpy
import operator

from activity_distribution import ActivityDistribution
from stats import Stats
from static import DAYS


class Plot(object):
    """Generates plots from the Stats modules."""

    @injector.inject(activity_distribution=ActivityDistribution, stats=Stats)
    def __init__(self, activity_distribution, stats):
        super(Plot, self).__init__()
        self._activity_distribution = activity_distribution
        self._stats = stats

    def plot_generic_histogram(self, histogram, key='mean'):
        stats = self._stats.get_hourly_statistics(histogram)
        fig = plt.figure()
        self._plot_run(
            fig,
            None,
            [i[key] for i in stats],
            '%s (%s)' % (histogram, key), 111)
        fig.set_size_inches(6, 5)
        fig.set_tight_layout(True)
        fig.savefig('inactivity_%s_%s.png' % (histogram.lower(), key.lower()))

    # pylint: disable=invalid-name
    def plot_activity_means_and_medians(self):
        """Plots the activity means and medians in two plots."""
        stats = self._stats.get_hourly_statistics('SERVING_TIME')
        fig = plt.figure()
        self._plot_run(
            fig,
            self._activity_distribution.activity_means(),
            [i['mean'] for i in stats],
            'means comparison', 121,
            unit='Activity interval length (s)')
        self._plot_run(
            fig,
            self._activity_distribution.activity_medians(),
            [i['median'] for i in stats],
            'medians comparison', 122,
            unit='Activity interval length (s)')
        fig.set_size_inches(12, 5)
        fig.set_tight_layout(True)
        fig.savefig('activity_means_and_medians.png')

    # pylint: disable=invalid-name
    def plot_inactivity_means_and_medians(self):
        """Plots the inactivity means and medians in two plots."""
        stats = self._stats.get_hourly_statistics('INACTIVITY_TIME_ACCURATE')
        fig = plt.figure()
        self._plot_run(
            fig,
            self._activity_distribution.inactivity_means(),
            [i['mean'] for i in stats],
            'means comparison', 121,
            unit='Inactivity interval length (s)')
        self._plot_run(
            fig,
            self._activity_distribution.inactivity_medians(),
            [i['median'] for i in stats],
            'medians comparison', 122,
            unit='Inactivity interval length (s)')
        fig.set_size_inches(12, 5)
        fig.set_tight_layout(True)
        fig.savefig('inactivity_means_and_medians.png')

    # pylint: disable=invalid-name
    def plot_inactivity_counts_and_shutdowns(self):
        """Plots the cunt of inactivity events and the shutdown events."""
        stats = self._stats.get_hourly_statistics('INACTIVITY_TIME_ACCURATE')
        stats2 = self._stats.get_hourly_statistics('SHUTDOWN_INTERVAL')
        fig = plt.figure()
        self._plot_run(
            fig,
            self._activity_distribution.inactivity_counts(),
            [i['count'] for i in stats],
            'interval count comparison', 121,
            unit='Interval count')
        self._plot_run(
            fig,
            self._activity_distribution.shutdown_counts(),
            [i['count'] for i in stats2],
            'shutdown event count comparison', 122,
            unit='Shutdown events count')
        fig.set_size_inches(12, 5)
        fig.set_tight_layout(True)
        fig.savefig('inactivity_counts_and_shutdowns.png')

    # pylint: disable=too-many-arguments
    def _plot_run(self, fig, real_data, simulation_data, label, subplot=111,
                  unit=None):
        """Internal implementation of the plot generation."""
        # pylint: disable=invalid-name
        ax = fig.add_subplot(subplot)
        ax.set_title(label)
        # pylint: disable=no-member
        if real_data:
            ax.plot(numpy.linspace(1, len(real_data), len(real_data)),
                    real_data,
                    'r-',
                    label='real data')
        # pylint: disable=no-member
        ax.plot(numpy.linspace(1, len(simulation_data), len(simulation_data)),
                simulation_data,
                'g-',
                label='simulated data')
        self._format_ax_line(ax)
        if unit:
            ax.set_ylabel(unit)

    # pylint: disable=no-self-use
    def _format_ax_line(self, ax):
        """Common format for each of the axes."""
        ax.legend(loc='upper center', fontsize=8)
        ax.set_xlim(0, 7 * 24 - 1)
        ax.set_xticks(numpy.arange(7) * 24)  # pylint: disable=no-member
        ax.set_xticklabels(
            [key for key, _ in sorted(DAYS.items(),
                                      key=operator.itemgetter(1))], rotation=60)
