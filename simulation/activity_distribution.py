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

"""User (in)activity distribution parsing, fitting and generation."""

import functools
import itertools
import json
import logging
import operator
import typing
import injector
import numpy
from simulation.configuration import Configuration
from simulation.fleet_generator import FleetGenerator
from simulation.model import Model
from simulation.static import DAYS
from simulation.static import HISTOGRAMS
from simulation.static import WEEK
from simulation.static import draw_from_distribution
from simulation.static import previous_hour
from simulation.static import timed
from simulation.static import timestamp_to_day

logger = logging.getLogger(__name__)


class ActivityDistributionBase(object):
    """Stores the hourly activity distribution over a week.

    Each bucket of the histogram contains the distribution of the log file
    processed. Each bucket represents one hour of the week.
    """

    @injector.inject
    @injector.noninjectable('config_section')
    def __init__(self, config: Configuration,
                 model_builder: injector.ClassAssistedBuilder[Model],
                 config_section: str):
        """All the data of this object is loaded from the config object."""
        super(ActivityDistributionBase, self).__init__()
        self.__target_satisfaction = config.get_config_int(
            'target_satisfaction')
        self.__satisfaction_threshold = config.get_config_int(
            'satisfaction_threshold')
        self.__config = config
        self.__config_section = config_section
        do_merge = (config_section == 'training_distribution')
        self.__merge_by_pc = config.get_arg('merge_by_pc') and do_merge
        self.__merge_by_hour = config.get_arg('merge_by_hour') and do_merge
        self.__trace_file = config.get_config('file', section=config_section)
        self.__xmin = config.get_config_float('xmin', section=config_section)
        self.__xmax = config.get_config_float('xmax', section=config_section)
        self.__duration = config.get_config_float(
            'duration', section=config_section)
        self.__model_builder = functools.partial(
            model_builder.build, xmax=self.__xmax, xmin=self.__xmin)
        self.__servers = []
        self.__models = {}
        self.__optimal_timeout = None
        self.__optimal_timeouts = {}
        self.__parse_trace()

    @property
    def servers(self) -> typing.List[str]:
        """Read only servers list."""
        return self.__servers

    def test_timeout(self, timeouts):
        """Calculate analytically the US and RI for a given timeout."""
        all_wus = []
        all_us = []
        all_ri = 0.0
        all_ti = 0.0
        for cid, days in timeouts.items():
            for day, hours in days.items():
                for hour, t in hours.items():
                    model = self.__get(cid, day, hour)
                    if model is not None and model.is_complete:
                        wus, us, ri, ti = model.test_timeout(t, retest=True)
                        all_wus.append(wus)
                        all_us.append(us)
                        all_ri += ri
                        all_ti += ti
                    else:
                        all_ri += 3600 - min(t, 1800)
                        all_ti += 3600
        return (numpy.mean(all_wus), numpy.median(all_wus), numpy.std(all_wus),
                numpy.mean(all_us), numpy.median(all_us), numpy.std(all_us),
                all_ri / all_ti * 100)

    def all_idle_timeouts(self):
        self.global_idle_timeout()
        return self.__optimal_timeouts

    def graph_results(self, min_t, max_t, step):
        # example: min_t = 0, max_t = 20*60, step=30
        with open('graphic.csv', 'w') as f:
            f.write('t;wus_mean;wus_median;wus_std;us_mean;us_median;us_std;ri\n')
            for t in range(min_t, max_t, step):
                logger.info('Testing timeout %d...', t)
                metrics = [str(i).replace('.', ',') for i in
                           self.test_timeout(self.construct_timeouts(t))]
                f.write("%d;%s\n" % (t, ';'.join(metrics)))
                logger.info('Done.')

    def construct_timeouts(self, t):
        timeouts = {}
        for cid, days in self.__models.items():
            timeouts[cid] = {}
            for day, hours in days.items():
                timeouts[cid][day] = {}
                for hour in hours.keys():
                    timeouts[cid][day][hour] = t
        return timeouts

    def global_idle_timeout(self) -> float:
        """Calculates the value of the idle timer for a given satisfaction."""
        if self.__optimal_timeout is None:
            timeouts = []
            for cid, days in self.__models.items():
                self.__optimal_timeouts[cid] = {}
                for day, hours in days.items():
                    self.__optimal_timeouts[cid][day] = {}
                    for hour in hours.keys():
                        model = self.__distribution_for_hour(cid, day, hour)
                        if model:
                            t = model.optimal_idle_timeout()
                            self.__optimal_timeouts[cid][day][hour] = t
                            timeouts.append(t)
            self.__optimal_timeout = (numpy.mean(timeouts),
                                      numpy.median(timeouts),
                                      numpy.std(timeouts))
        return self.__optimal_timeout

    def optimal_idle_timeout(self, cid: str) -> float:
        """Calculates the value of the idle timer for a given satisfaction."""
        return self.__optimal_timeout_timestamp(
            cid, *timestamp_to_day(self.__config.env.now))

    def random_activity_for_timestamp(self, cid: str, timestamp: int) -> float:
        """Queries the activity distribution and generates a random sample."""
        return draw_from_distribution(
            self.__distribution_for_hour(
                cid, *timestamp_to_day(timestamp)).activity,
            min_value=0.1, max_value=self.__xmax)

    def random_inactivity_for_timestamp(
            self, cid: str, timestamp: int) -> float:
        """Queries the activity distribution and generates a random sample."""
        return draw_from_distribution(
            self.__distribution_for_hour(
                cid, *timestamp_to_day(timestamp)).inactivity,
            min_value=self.__xmin, max_value=self.__xmax)

    def off_interval_for_timestamp(self, cid: str, timestamp: int) -> float:
        """Samples an off interval for the day and hour provided"""
        return draw_from_distribution(
            self.__distribution_for_hour(
                cid, *timestamp_to_day(timestamp)).off_duration,
            min_value=self.__xmin, max_value=self.__xmax)

    def off_frequency_for_hour(self, cid: str, day: int, hour: int) -> float:
        """Determines whether a computer should turndown or not."""
        return numpy.mean(
            self.__distribution_for_hour(cid, day, hour).off_fraction)

    def get_all_hourly_percentiles(
            self, key: str, percentile: float) -> typing.List[float]:
        """Returns the requested percentile per hour."""
        percentiles = []
        transposed = self.__transpose_histogram()
        for day in range(7):
            for hour in range(24):
                try:
                    percentiles.append(numpy.percentile(
                        [d for i in transposed.get(day, {}).get(hour, [])
                         for d in i.resolve_key(key)], percentile))
                except IndexError:
                    percentiles.append(0.0)
        return percentiles

    def get_all_hourly_count(self, key: str) -> typing.List[int]:
        """Returns the counts per hour."""
        hours = []
        transposed = self.__transpose_histogram()
        for day in range(7):
            for hour in range(24):
                total = sum(len(i.resolve_key(key))
                            for i in transposed.get(day, {}).get(hour, []))
                total /= len(self.__servers)
                if self.__merge_by_hour:
                    total /= 168
                if self.__merge_by_pc:
                    total /= len(self.__servers)
                total /= self.__duration / WEEK(1)
                hours.append(total)
        return hours

    def get_all_hourly_distributions(self):
        """Returns all the intervals per day, hour and key."""
        transposed = {}
        for days in self.__models.values():
            for day, hours in days.items():
                for hour, model in hours.items():
                    for key in HISTOGRAMS:
                        data = model.resolve_key(key).data
                        if len(data) > 0:
                            dct = transposed.setdefault(
                                key, {}).setdefault(day, {})
                            dct.setdefault(
                                hour, numpy.append(dct.get(hour, []), data))
        return transposed

    def __get_flat_model(self, cid: str = None) -> Model:
        """Create a model with all of the data of a given computer (or all)."""
        flat_models = self.__get_unique_models(cid)
        if len(flat_models) > 1:
            flat = self.__model_builder()
            flat.extend(flat_models)
            return flat
        return flat_models[0]

    def __get_unique_models(self, cid: str = None) -> typing.List[Model]:
        """Fetches and filters the models for a given cid (or all)."""
        models = set()
        for days in [self.__models[cid]] if cid else self.__models.values():
            for day, hours in days.items():
                for hour, model in hours.items():
                    models.add(model)
        return list(models)

    def __optimal_timeout_all(self, cid: str) -> float:
        """Calculate the optimal timeout for all the simulation."""
        return self.__get_flat_model(cid).optimal_idle_timeout()

    def __optimal_timeout_timestamp(
            self, cid: str, day: int, hour: int) -> float:
        """Calculate the optimal timestamp for a given timestamp."""
        hist = self.__distribution_for_hour(cid, day, hour)
        if hist is None:
            return self.__optimal_timeout_all(cid)
        return hist.optimal_idle_timeout()

    def __distribution_for_hour(self, cid: str, day: int, hour: int) -> Model:
        previous_count = 0
        d, h = day, hour
        distribution = self.__get(cid, d, h)
        if distribution is None or not distribution.is_complete:
            while distribution is None or not distribution.is_complete:
                if previous_count > 168:
                    logger.warning('There is no model for %s (%d,%d)',
                                   cid, day, hour)
                    return None
                previous_count += 1
                d, h = previous_hour(d, h)
                distribution = self.__get(cid, d, h)
            self.__models[cid].setdefault(day, {}).setdefault(
                hour, distribution)
        return distribution

    def __transpose_histogram(
            self) -> typing.Dict[int, typing.Dict[int, typing.List[float]]]:
        """Converts the {PC: {Day: {Hour: x}}} hist to {Day: {Hour: [x*]}}."""
        transposed = {}
        for day in range(7):
            for hour in range(24):
                for value in self.__models.values():
                    if value.get(day, {}).get(hour) is not None:
                        transposed.setdefault(day, {}).setdefault(
                            hour, []).append(value.get(day, {}).get(hour))
        return transposed

    @timed
    def __parse_trace(self) -> None:
        """Parses the json trace to generate all the histograms."""
        logger.debug('Parsing models.')
        with open(self.__trace_file) as trace:
            trace = json.load(trace)
            trace = [i for i in trace if i['PC'] != '_Total']
            key = operator.itemgetter('PC')
            self.__models = {}
            for pc, trace in itertools.groupby(
                    sorted(trace, key=key), key=key):
                self.__servers.append(pc)
                self.__models[pc] = self.__parse_model(
                    {t['Type']: t['data'] for t in trace})
            if len(self.__servers) != len(set(self.__servers)):
                raise ValueError('There are duplicate PCs')
        self.__merge_histograms()

    def __parse_model(
            self,
            traces: typing.Dict[str, typing.List[typing.Dict[str, typing.Any]]]
    ) -> typing.Dict[int, typing.Dict[int, Model]]:
        """Generic parser of a server model."""
        histogram = {}
        for t, data in traces.items():
            for d in data:
                day = DAYS[d['Day']]
                hour = int(d['Hour'])
                histogram.setdefault(day, {}).setdefault(
                    hour, {})[t] = self.__filter(t, d['Intervals'])
        models = {}
        for day, hours in histogram.items():
            for hour, dct in hours.items():
                models.setdefault(day, {}).setdefault(
                    hour, self.__model_builder(
                        inactivity=dct['InactivityIntervals'],
                        activity=dct['ActivityIntervals'],
                        off_duration=dct['OffIntervals'],
                        off_fraction=dct['OffFrequencies']))
        return models

    def __filter(self, t: str, data: typing.List[float]) -> typing.List[float]:
        """Perform filtering on the raw data to improve quality."""
        if t == 'InactivityIntervals':
            data = (i for i in data if self.__xmin <= i <= self.__xmax)
        if t != 'OffFrequencies':
            data = (i for i in data if i > 0)
        return list(data)

    def __merge_histograms(self) -> None:
        """Merges histograms to be global or per PC/hour."""
        if self.__merge_by_hour and self.__merge_by_pc:
            logger.info('%s: Merging histogram both per hour and PC.',
                        self.__config_section)
            self.__merge_per_hour_and_pc()
        elif self.__merge_by_hour:
            logger.info('%s: Merging histogram per hour.',
                        self.__config_section)
            self.__merge_per_hour()
        elif self.__merge_by_pc:
            logger.info('%s: Merging histogram per PC.',
                        self.__config_section)
            self.__merge_per_pc()
        else:
            logger.info('%s: Will not merge any dataset.',
                        self.__config_section)

    def __merge_per_hour(self) -> None:
        """Merge so all hours have the same model."""
        merged = {}
        for days in self.__models.values():
            for day, hours in days.items():
                for hour, model in hours.items():
                    merged.setdefault(day, {}).setdefault(
                        hour, []).append(model)
        for day, hours in merged.items():
            for hour, models in hours.items():
                merged_model = self.__model_builder()
                merged_model.extend(models)
                merged[day][hour] = merged_model
        for cid in self.__models:
            self.__models[cid] = merged

    def __merge_per_pc(self) -> None:
        """Merge so all PCs have the same model."""
        merged = {}
        for cid, days in self.__models.items():
            models = []
            for day, hours in days.items():
                for hour, model in hours.items():
                    models.append(model)
            merged_model = self.__model_builder()
            merged_model.extend(models)
            merged[cid] = {d: {h: merged_model for h in range(24)}
                           for d in range(7)}
        self.__models = merged

    def __merge_per_hour_and_pc(self) -> None:
        """Merge so all PCs and hours have the same model."""
        models = []
        for cid, days in self.__models.items():
            for day, hours in days.items():
                for hour, model in hours.items():
                    models.append(model)
        merged_model = self.__model_builder()
        merged_model.extend(models)
        self.__models = {cid: {d: {h: merged_model for h in range(24)}
                               for d in range(7)}
                         for cid in self.__models.keys()}

    def __get(self, cid: int, day: int, hour: int) -> Model:
        """Generic getter for a model."""
        try:
            return self.__models[cid][day][hour]
        except KeyError:
            return None


@injector.singleton
class DistributionFactory(object):
    """Creates distribution objects based on the command line flags."""

    @injector.inject
    def __init__(self, config: Configuration,
                 distr_builder: injector.ClassAssistedBuilder[
                     ActivityDistributionBase],
                 fleet_generator: FleetGenerator):
        super(DistributionFactory, self).__init__()
        self.__activity_distr = distr_builder.build(
                config_section='activity_distribution')
        self.__training_distr = distr_builder.build(
                config_section='training_distribution')
        self.__fleet_generator = fleet_generator
        self.__is_fleet_generator = config.get_arg('fleet_generator')

    def __call__(self, training=False):
        """Return one of the distribution objects as needed."""
        if self.__is_fleet_generator:
            return self.__fleet_generator
        if training:
            return self.__training_distr
        return self.__activity_distr
