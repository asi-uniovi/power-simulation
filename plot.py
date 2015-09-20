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

    def plot_inactivity_means_and_medians(self):
        fig = plt.figure()
        self._plot_run(
            fig,
            self._activity_distribution.inactivity_means(),
            self._stats.means_for_histogram('INACTIVITY_TIME_ACCURATE'),
            'means comparison', 121)
        self._plot_run(
            fig,
            self._activity_distribution.inactivity_medians(),
            self._stats.medians_for_histogram('INACTIVITY_TIME_ACCURATE'),
            'medians comparison', 122)
        fig.set_size_inches(12, 5)
        fig.set_tight_layout(True)
        fig.savefig('inactivity_means_and_medians.png')

    def _plot_run(self, fig, real_data, simulation_data, label, subplot=111):
        ax = fig.add_subplot(subplot)
        ax.plot(numpy.linspace(1, len(real_data), len(real_data)),
                real_data,
                'r-',
                label='real data')
        ax.plot(numpy.linspace(1, len(simulation_data), len(simulation_data)),
                simulation_data,
                'g-',
                label='simulated data')
        self._format_ax_line(ax)

    def _format_ax_line(self, ax):
        ax.legend(loc='upper center', fontsize=8)
        ax.set_xlim(0, 7 * 24 - 1)
        ax.set_xticks(numpy.arange(7) * 24)
        ax.set_ylabel('Inactivity interval length (s)')
        ax.set_xticklabels(
            [key for key, _ in sorted(DAYS.items(),
                                      key=operator.itemgetter(1))],
            rotation=60)
