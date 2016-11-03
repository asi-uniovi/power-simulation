"""Summarizes the stats collected during the simulation in plots."""

import logging
import operator
import typing
import injector
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy
from activity_distribution import TrainingDistribution
from static import DAYS
from stats import Stats

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


# pylint: disable=no-member,invalid-name
class Plot:
    """Generates plots from the Stats modules."""

    @injector.inject
    def __init__(self, training_distribution: TrainingDistribution,
                 stats: Stats):
        self.__training_distribution = training_distribution
        self.__stats = stats

    def plot_all(self, histogram: str) -> None:
        """Plots all the available plots."""
        try:
            self.plot_hourly_histogram_count(histogram)
            self.plot_mean_medians_comparison(histogram)
            self.plot_hourly_histogram_quantiles(histogram)
        except KeyError:
            logger.warning('Histogram %s produced no plot.', histogram)

    def plot_hourly_histogram_quantiles(
            self, histogram: str,
            quantiles: typing.Tuple[int]=(50, 75, 80, 90, 95, 99)) -> None:
        """Generates a plot to see the hourly quantiles."""
        fig, ax = plt.subplots()
        ax.set_title(histogram + ' (percentiles)')
        ax.set_xlim(0, 7 * 24 - 1)

        hists = self.__stats.get_all_hourly_histograms(histogram)
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
        plt.close(fig)

    def plot_mean_medians_comparison(self, histogram: str) -> None:
        """Generates a plot to compare means and medians."""
        hist = self.__stats.get_all_hourly_summaries(histogram)
        data = self.__training_distribution.get_all_hourly_summaries(histogram)

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
            plt.close(fig)

    def plot_hourly_histogram_count(self, histogram: str) -> None:
        """Generates a plot to show the hourly counts."""
        hist = self.__stats.get_all_hourly_count(histogram)
        data = self.__training_distribution.get_all_hourly_count(histogram)

        fig, ax = plt.subplots()
        ax.set_title('%s (count)' % histogram)
        ax.set_xlim(0, 7 * 24 - 1)

        ax.plot(numpy.linspace(1, len(hist), len(hist)), hist,
                label='simulation')
        ax.plot(numpy.linspace(1, len(data), len(data)), data, label='data')

        _format_ax_line(ax)
        fig.set_size_inches(6, 5)
        fig.set_tight_layout(True)
        fig.savefig('%s_count.png' % histogram.lower())
        plt.close(fig)

# pylint: disable=invalid-name
def _format_ax_line(ax) -> None:
    """Common format for each of the axes."""
    ax.legend(loc='upper center', fontsize=8)
    ax.grid(True)
    ax.set_xticks(numpy.arange(7) * 24)
    ax.set_xticklabels(
        [key for key, _ in sorted(DAYS.items(),
                                  key=operator.itemgetter(1))], rotation=60)
