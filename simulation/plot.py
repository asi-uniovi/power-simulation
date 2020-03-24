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

import collections
import injector
import logging
import matplotlib.pyplot as plt
import numpy
import operator
from simulation.activity_distribution import DistributionFactory
from simulation.base import Base
from simulation.static import DAYS
from simulation.static import HISTOGRAMS
from simulation.static import REVERSE_DAYS
from simulation.static import hour_to_day
from simulation.static import timed
from simulation.static import timestamp_to_hour
from simulation.stats import Stats

logger = logging.getLogger(__name__)


@injector.singleton
class Plot(Base):
    """Generates plots from the Stats modules."""

    @injector.inject
    def __init__(
            self, distribution_factory: DistributionFactory, stats: Stats):
        super(Plot, self).__init__()
        self.__activity_distribution = distribution_factory()
        self.__training_distribution = distribution_factory(training=True)
        self.__stats = stats

    @timed
    def plot_all(self) -> None:
        """Plots all the available plots."""
        self.plot_hourly_time_percentages()
        for histogram in HISTOGRAMS:
            self.plot_mean_medians_comparison(histogram)

    @timed
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

    @timed
    def plot_hourly_time_percentages(self):
        """Plots the time percentages as percentual bar charts."""
        stats = self.__generate_events2()
        bar_s = [i * 1.05 for i in range(0, 48, 2)]

        figure, axes = plt.subplots(nrows=7, sharex='col')

        axesd = collections.deque(axes)
        axesd.rotate(1)
        for day, axis in enumerate(axesd):
            self.__plot_bar(axis, bar_s, stats.get(day))
            axis.set_xticks(bar_s)
            axis.set_xticklabels(range(24))
            axis.set_ylim(0, 100)
            axis.set_title(REVERSE_DAYS[day])

        axesd[0].legend(loc='center', bbox_to_anchor=(0.5, -1), ncol=2)
        figure.set_size_inches(6.5, 11)
        figure.set_tight_layout(True)
        figure.savefig('hourly_time_percentages.png')
        plt.close(figure)

    def __plot_bar(self, axis, bar, hist, orig=False):
        """Plot a daily bar chart."""
        bottom = numpy.asarray([0.0] * 24)
        COLORS = {
            'ACTIVITY_TIME': 'tab:blue',
            'INACTIVITY_TIME': 'tab:orange',
            'USER_SHUTDOWN_TIME': 'lightgrey',
            'AUTO_SHUTDOWN_TIME': 'dimgray',
        }
        suffix = ''
        width = 2
        for key in HISTOGRAMS:
            data = [hist[h][key] / hist[h]['TOTAL'] * 100 for h in range(24)]
            axis.bar(bar, data, width=width, bottom=bottom, label=key + suffix,
                     color=COLORS[key], hatch='////' if orig else None)
            bottom = bottom + data

    def __process_pc_intervals(self, intervals):
        """Buckets and cuts the intervals of a PC, which are given sorted."""
        processed = collections.defaultdict(
            lambda: collections.defaultdict(list))
        for key, timestamp, interval in sorted(
                intervals, key=operator.itemgetter(1)):
            hour = timestamp_to_hour(timestamp)
            used = timestamp % 3600
            if (used + interval) <= 3600.0:
                processed[hour][key].append(interval)
            else:
                half = 3600 - used
                processed[hour][key].append(half)
                remaining = interval - half
                extra_hours = int(remaining // 3600)
                for i in range(extra_hours):
                    processed[(hour + i + 1) % 168][key].append(3600)
                processed[(hour + extra_hours + 1) % 168][key].append(
                    remaining % 3600)
        return processed

    def __generate_events2(self):
        """Generate the buckets of events per hour."""
        buckets = collections.defaultdict(
            lambda: collections.defaultdict(
                lambda: collections.defaultdict(float)))
        for intervals in self.__stats.get_merged_events().values():
            for hour, keys in self.__process_pc_intervals(intervals).items():
                d, h = hour_to_day(hour)
                for key, events in keys.items():
                    buckets[d][h][key] += sum(events)
                    buckets[d][h]['TOTAL'] += sum(events)
        return buckets
