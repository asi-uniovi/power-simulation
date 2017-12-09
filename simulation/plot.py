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

"""Summarizes the stats collected during the simulation in plots."""

import logging
import operator
import injector
import matplotlib.pyplot as plt
import numpy
from simulation.activity_distribution import DistributionFactory
from simulation.base import Base
from simulation.static import DAYS
from simulation.static import HISTOGRAMS
from simulation.stats import Stats

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@injector.singleton
class Plot(Base):
    """Generates plots from the Stats modules."""

    @injector.inject
    def __init__(self, distribution_factory: DistributionFactory, stats: Stats):
        super(Plot, self).__init__()
        self.__training_distribution = distribution_factory(training=True)
        self.__stats = stats

    def plot_all(self) -> None:
        """Plots all the available plots."""
        self.plot_hourly_time_percentages()
        for histogram in HISTOGRAMS:
            self.plot_mean_medians_comparison(histogram)

    def plot_hourly_time_percentages(self):
        """Plots the time percentages as percentual bar charts."""
        hists = self.__generate_hourly_time_percentages(
            self.__training_distribution.get_all_hourly_distributions())
        stats = self.__generate_hourly_time_percentages(
            self.__stats.get_all_hourly_distributions())

        figure, axes = plt.subplots(nrows=7, sharex='col')
        bar_h = [i * 1.05 for i in range(0, 48, 2)]
        bar_s = [i + 1 for i in bar_h]

        for day, axis in enumerate(axes):
            self.plot_bar(axis, bar_h, hists.get(day))
            self.plot_bar(axis, bar_s, stats.get(day))
            axis.set_xticks([i + 1/2 for i in bar_h])
            axis.set_xticklabels(range(24))
            axis.set_ylim(0, 100)

        figure.set_size_inches(6.5, 10)
        figure.set_tight_layout(True)
        figure.savefig('hourly_time_percentages.png')
        plt.close(figure)

    # pylint: disable=blacklisted-name,invalid-name,no-self-use
    def plot_bar(self, axis, bar, hist):
        """Plot a daily bar chart."""
        bottom = numpy.asarray([0.0] * 24)
        COLORS = {
            'ACTIVITY_TIME': 'g',
            'INACTIVITY_TIME': 'r',
            'USER_SHUTDOWN_TIME': 'b',
            'AUTO_SHUTDOWN_TIME': 'y',
        }
        for key in HISTOGRAMS:
            data = [hist[key][h] for h in range(24)]
            axis.bar(bar, data, width=1.0, bottom=bottom, label=key,
                     color=COLORS[key])
            bottom = bottom + data

    def plot_mean_medians_comparison(self, histogram: str) -> None:
        """Generates a plot to compare means and medians."""
        for percentile in (50, 75, 90, 99):
            figure, axis = plt.subplots()
            stats = self.__stats.get_all_hourly_percentiles(
                histogram, percentile)
            axis.plot(numpy.linspace(1, len(stats), len(stats)), stats,
                      label='simulation', linewidth=3)
            hists = self.__training_distribution.get_all_hourly_percentiles(
                histogram, percentile)
            axis.plot(numpy.linspace(1, len(hists), len(hists)), hists,
                      label='data', linewidth=1)
            axis.set_title('%s (p%d)' % (histogram, percentile))
            axis.set_xlim(0, 7 * 24 - 1)
            axis.legend(loc='upper center', fontsize=8)
            axis.grid(True)
            axis.set_xticks(numpy.arange(7) * 24)
            axis.set_xticklabels(
                [key for key, _ in sorted(
                    DAYS.items(), key=operator.itemgetter(1))], rotation=60)
            figure.set_size_inches(6, 5)
            figure.set_tight_layout(True)
            figure.savefig('%s_p%d.png' % (histogram.lower(), percentile))
            plt.close(figure)

    # pylint: disable=no-self-use
    def __generate_carry_over(self, intervals):
        carry_over, new_intervals = [], []
        for i in intervals:
            if i <= 3600:
                new_intervals.append(i)
            else:
                carry_over.append(i - 3600)
                new_intervals.append(3600)
        return carry_over, new_intervals

    # pylint: disable=too-many-locals
    def __generate_hourly_time_percentages(self, hist):
        """Calculates the percentage with carry over for the time spent."""
        totals = {}
        key_totals = {}
        for key, days in hist.items():
            previous_carry_over = []
            for day, hours in days.items():
                for hour, intervals in hours.items():
                    carry_over, new_intervals = self.__generate_carry_over(
                        intervals)
                    total = numpy.sum(new_intervals + previous_carry_over)
                    previous_carry_over = carry_over
                    dct = key_totals.setdefault(day, {}).setdefault(hour, {})
                    dct[key] = total
                    dct = totals.setdefault(day, {})
                    dct[hour] = dct.get(hour, 0.0) + total
        percentages = {}
        for day, hours in key_totals.items():
            for hour, keys in hours.items():
                for key, total in keys.items():
                    percentages.setdefault(day, {}).setdefault(
                        key, {}).setdefault(
                            hour, total / totals[day][hour] * 100)
        for day in range(7):
            for key in HISTOGRAMS:
                for hour in range(24):
                    percentages.setdefault(day, {}).setdefault(
                        key, {}).setdefault(hour, 0.0)
        return percentages
