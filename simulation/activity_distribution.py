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

import abc
import functools
import itertools
import json
import logging
import operator
import typing
import injector
import numpy
from simulation.base import Base
from simulation.distribution import EmpiricalDistribution
from simulation.fleet_generator import FleetGenerator
from simulation.model import Model
from simulation.static import DAYS
from simulation.static import HISTOGRAMS
from simulation.static import WEEK
from simulation.static import draw_from_distribution
from simulation.static import timed
from simulation.static import timestamp_to_day

logger = logging.getLogger(__name__)


def previous_hour(day: int, hour: int) -> typing.Tuple[int, int]:
    """Gets the previous hour with wrap."""
    hour -= 1
    if hour < 0:
        hour = 23
        day -= 1
        if day < 0:
            day = 6
    return day, hour


class ActivityDistributionBase(Base, metaclass=abc.ABCMeta):
    """Stores the hourly activity distribution over a week.

    Each bucket of the histogram contains the distribution of the log file
    processed. Each bucket represents one hour of the week.
    """

    @injector.inject
    @injector.noninjectable('config_section')
    def __init__(self, model_builder: injector.ClassAssistedBuilder[Model],
                 config_section: str):
        """All the data of this object is loaded from the config object."""
        super(ActivityDistributionBase, self).__init__()
        self.__target_satisfaction = self.get_config_int('target_satisfaction')
        self.__satisfaction_threshold = self.get_config_int(
            'satisfaction_threshold')
        self.__trace_file = self.get_config('file', section=config_section)
        self.__xmin = self.get_config_float('xmin', section=config_section)
        self.__xmax = self.get_config_float('xmax', section=config_section)
        self.__duration = self.get_config_float(
            'duration', section=config_section)
        self.__model_builder = functools.partial(
            model_builder.build, xmax=self.__xmax, xmin=self.__xmin)
        self.__servers = []
        self.__models = {}
        self.__optimal_timeout = None
        self.__parse_trace()

    @property
    def servers(self) -> typing.List[str]:
        """Read only servers list."""
        return self.__servers

    def test_timeout(self, timeout: float) -> typing.Tuple[float, float, float]:
        """Calculate analytically the US and RI for a given timeout."""
        return self.__get_flat_model().test_timeout(timeout)

    def global_idle_timeout(self) -> float:
        """Calculates the value of the idle timer for a given satisfaction."""
        if self.__optimal_timeout is None:
            self.__optimal_timeout = numpy.mean([self.optimal_idle_timeout(
                cid, all_timespan=True) for cid in self.__servers])
        return self.__optimal_timeout

    def optimal_idle_timeout(
            self, cid: str, all_timespan: bool = False) -> float:
        """Calculates the value of the idle timer for a given satisfaction."""
        if all_timespan:
            return self.__optimal_timeout_all(cid)
        return self.__optimal_timeout_timestamp(
            cid, *timestamp_to_day(self.env.now))

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
                if not self.get_arg('per_hour'):
                    total /= 168
                if not self.get_arg('per_pc'):
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
        """Queries the activity distribution to the get average inactivity."""
        previous_count = 0
        d, h = day, hour
        distribution = self.__get(cid, d, h)
        if distribution is None:
            while distribution is None:
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
        if not self.get_arg('per_hour') and not self.get_arg('per_pc'):
            logger.info('Merging histogram both per hour and PC.')
            self.__merge_per_hour_and_pc()
        elif not self.get_arg('per_hour'):
            logger.info('Merging histogram per hour.')
            self.__merge_per_hour()
        elif not self.get_arg('per_pc'):
            logger.info('Merging histogram per PC.')
            self.__merge_per_pc()
        else:
            logger.info('Will not merge any dataset.')

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
class ActivityDistribution(ActivityDistributionBase):
    """Activity distribution for tracing purposes."""

    def __init__(self):
        super(ActivityDistribution, self).__init__(
            config_section='activity_distribution')


@injector.singleton
class TrainingDistribution(ActivityDistributionBase):
    """Activity distribution for training purposes."""

    def __init__(self):
        super(TrainingDistribution, self).__init__(
            config_section='training_distribution')


@injector.singleton
class DistributionFactory(Base):
    """Creates distribution objects based on the command line flags."""

    @injector.inject
    def __init__(self, activity_distribution: ActivityDistribution,
                 training_distribution: TrainingDistribution,
                 fleet_generator: FleetGenerator):
        super(DistributionFactory, self).__init__()
        self.__activity_distribution = activity_distribution
        self.__training_distribution = training_distribution
        self.__fleet_generator = fleet_generator

    def __call__(self, training=False):
        """Return one of the distribution objects as needed."""
        if self.get_arg('fleet_generator'):
            return self.__fleet_generator
        if training:
            return self.__training_distribution
        return self.__activity_distribution
