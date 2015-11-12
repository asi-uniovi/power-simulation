"""Summarizes the stats collected during the simulation in plots."""

import injector
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy
import operator

from activity_distribution import ActivityDistribution
from stats import Stats
from static import DAYS


@injector.inject(_activity_distribution=ActivityDistribution, _stats=Stats)
class Plot(object):
    """Generates plots from the Stats modules."""

    def plot_hourly_histogram_quantiles(
            self, histogram, quantiles=(50, 75, 80, 90, 95, 99)):
        fig, ax = plt.subplots()
        ax.set_title(histogram + ' (percentiles)')
        ax.set_xlim(0, 7 * 24 - 1)

        hists = self._stats.get_all_hourly_histograms(histogram)
        for p in quantiles:
            data = []
            for h in hists:
                try:
                    data.append(numpy.percentile(h, p))
                except IndexError:
                    data.append(0)

            ax.plot(numpy.linspace(1, len(data), len(data)), data,
                    label='%d%%' % p, color=cm.hot(1.0 - p / 100.0))

        _format_ax_line(ax)
        fig.set_size_inches(6, 5)
        fig.set_tight_layout(True)
        fig.savefig('%s_percentiles.png' % histogram.lower())

    def plot_mean_medians_comparison(self, histogram):
        hist = self._stats.get_all_hourly_summaries(histogram)
        data = self._activity_distribution.get_all_hourly_summaries(histogram)

        for s in ('mean', 'median'):
            fig, ax = plt.subplots()
            ax.set_title('%s (%s)' % (histogram, s))
            ax.set_xlim(0, 7 * 24 - 1)

            for d, label in ((hist, 'simulation'), (data, 'data')):
                f = [i[s] for i in d]
                ax.plot(numpy.linspace(1, len(f), len(f)), f, label=label)

            _format_ax_line(ax)
            fig.set_size_inches(6, 5)
            fig.set_tight_layout(True)
            fig.savefig('%s_%s.png' % (histogram.lower(), s))

    def plot_hourly_histogram_count(self, histogram):
        hist = self._stats.get_all_hourly_count(histogram)
        data = self._activity_distribution.get_all_hourly_count(histogram)

        fig, ax = plt.subplots()
        ax.set_title('%s (count)' % histogram)
        ax.set_xlim(0, 7 * 24 - 1)

        ax.plot(numpy.linspace(1, len(hist), len(hist)), hist, label='simulation')
        ax.plot(numpy.linspace(1, len(data), len(data)), data, label='data')

        _format_ax_line(ax)
        fig.set_size_inches(6, 5)
        fig.set_tight_layout(True)
        fig.savefig('%s_count.png' % histogram.lower())

def _format_ax_line(ax):
    """Common format for each of the axes."""
    ax.legend(loc='upper center', fontsize=8)
    ax.grid(True)
    ax.set_xticks(numpy.arange(7) * 24)  # pylint: disable=no-member
    ax.set_xticklabels(
        [key for key, _ in sorted(DAYS.items(),
                                  key=operator.itemgetter(1))], rotation=60)
