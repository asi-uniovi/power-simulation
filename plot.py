"""Summarizes the stats collected during the simulation in plots."""

import injector
import matplotlib.pyplot as plt
import numpy
import operator

from activity_distribution import ActivityDistribution
from stats import Stats
from static import DAYS


@injector.inject(_activity_distribution=ActivityDistribution, _stats=Stats)
class Plot(object):
    """Generates plots from the Stats modules."""

    def plot_generic_histogram(self, histogram):
        fig, ax = plt.subplots()
        ax.set_title(histogram)

        hists = self._stats.get_all_hourly_histograms(histogram)
        for p in (50, 75, 80, 90, 95, 99):
            data = []
            for h in hists:
                try:
                    data.append(numpy.percentile(h, p))
                except IndexError:
                    data.append(0)

            ax.plot(numpy.linspace(1, len(data), len(data)), data,
                    label='%d%%' % p)

        _format_ax_line(ax)
        fig.set_size_inches(6, 5)
        fig.set_tight_layout(True)
        fig.savefig('%s.png' % histogram.lower())


def _format_ax_line(ax):
    """Common format for each of the axes."""
    ax.legend(loc='upper center', fontsize=8)
    ax.grid(True)
    ax.set_xlim(0, 7 * 24 - 1)
    ax.set_xticks(numpy.arange(7) * 24)  # pylint: disable=no-member
    ax.set_xticklabels(
        [key for key, _ in sorted(DAYS.items(),
                                  key=operator.itemgetter(1))], rotation=60)
