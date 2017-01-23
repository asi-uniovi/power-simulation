"""User (in)activity distribution parsing, fitting and generation."""

import abc
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
from simulation.static import timestamp_to_day

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def previous_hour(day: int, hour: int) -> int:
    """Gets the previous hour with wrap."""
    hour -= 1
    if hour < 0:
        hour = 23
        day -= 1
        if day < 0:
            day = 6
    return day, hour


def draw_from_distribution(distribution: EmpiricalDistribution,
                           min_value: float=0,
                           max_value: float=float('inf')) -> float:
    """Gets a value from a distribution bounding the limit."""
    if distribution is None:
        return min_value
    rnd = distribution.rvs()
    while min_value >= rnd >= max_value:
        rnd = distribution.rvs()
    return rnd


# pylint: disable=too-many-instance-attributes
class ActivityDistributionBase(Base, metaclass=abc.ABCMeta):
    """Stores the hourly activity distribution over a week.

    Each bucket of the histogram contains the distribution of the log file
    processed. Each bucket represents one hour of the week.
    """

    @injector.inject
    def __init__(self, model_builder: injector.AssistedBuilder[Model],
                 do_merge: bool, trace_file: str):
        """All the data of this object is loaded from the config object."""
        super(ActivityDistributionBase, self).__init__()
        if self.get_arg('fleet_generator'):
            return
        self.__model_builder = model_builder
        self.__do_merge = do_merge
        self.__trace_file = self.get_config(trace_file, section='trace')
        self.__target_satisfaction = self.get_config_int('target_satisfaction')
        self.__satisfaction_threshold = self.get_config_int(
            'satisfaction_threshold', section='stats')
        self.__noise_threshold = self.get_config_float(
            'noise_threshold', section='trace')
        self.__xmin = self.get_config_float('xmin', section='trace')
        self.__xmax = self.get_config_float('xmax', section='trace')
        self.__servers = []
        self.__empty_servers = []
        # pylint: disable=invalid-name
        self.__models = {}
        self.__optimal_timeout = None
        self.__parse_trace()

    @property
    def servers(self) -> typing.List[str]:
        """Read only servers list."""
        return self.__servers

    @property
    def empty_servers(self) -> typing.List[str]:
        """Read only empty servers list."""
        return self.__empty_servers

    def intersect(self, other: 'ActivityDistributionBase') -> None:
        """Make this activity distribution intersect with other."""
        to_remove = set(self.empty_servers) | set(other.empty_servers)
        to_remove |= set(self.servers) ^ set(other.servers)
        self.remove_servers(to_remove)
        other.remove_servers(to_remove)

    def remove_servers(self, empty_servers: typing.List[str]) -> None:
        """Blacklist some of the servers."""
        self.__empty_servers = set(self.__empty_servers) | set(empty_servers)
        for cid in self.__empty_servers:
            if cid in self.__models:
                del self.__models[cid]
        self.__servers = sorted(set(self.__servers) - self.__empty_servers)
        self.__empty_servers = sorted(self.__empty_servers)

    def global_idle_timeout(self) -> float:
        """Calculates the value of the idle timer for a given satisfaction."""
        if self.__optimal_timeout is None:
            self.__optimal_timeout = numpy.mean([self.optimal_idle_timeout(
                cid, all_timespan=True) for cid in self.__servers])
        return self.__optimal_timeout

    def optimal_idle_timeout(self, cid: str, all_timespan: bool=False) -> float:
        """Calculates the value of the idle timer for a given satisfaction."""
        if all_timespan:
            return self.__optimal_timeout_all(cid)
        else:
            return self.__optimal_timeout_timestamp(
                cid, *timestamp_to_day(self._config.env.now))

    def random_activity_for_timestamp(self, cid: str, timestamp: int) -> float:
        """Queries the activity distribution and generates a random sample."""
        return draw_from_distribution(
            self.__distribution_for_hour(
                cid, *timestamp_to_day(timestamp)).activity,
            min_value=0.1, max_value=self.__xmax)

    def random_inactivity_for_timestamp(
            self, cid: str, timestamp: int) -> float:
        """Queries the activity distribution and generates a random sample."""
        distribution = self.__distribution_for_hour(
            cid, *timestamp_to_day(timestamp)).inactivity
        rnd_inactivity = draw_from_distribution(
            distribution, min_value=self.__xmin, max_value=self.__xmax)
        if self.__noise_threshold is not None:
            while rnd_inactivity > self.__noise_threshold:
                rnd_inactivity = draw_from_distribution(
                    distribution, min_value=self.__xmin, max_value=self.__xmax)
        return rnd_inactivity

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

    def get_all_hourly_summaries(
            self, key: str, summaries: dict=('mean', 'median')
    ) -> typing.List[typing.Dict[str, float]]:
        """Returns the summaries per hour."""
        hours = []
        transposed = self.__transpose_histogram()
        for day in range(7):
            for hour in range(24):
                data = numpy.array(
                    [d for i in transposed.get(day, {}).get(hour, [])
                     for d in i.resolve_key(key)])
                if len(data) > 0:
                    hours.append(
                        {s: getattr(numpy, s)(data) for s in summaries})
                else:
                    hours.append({s: 0.0 for s in summaries})
        return hours

    def get_all_hourly_count(self, key: str) -> typing.List[int]:
        """Returns the counts per hour."""
        hours = []
        transposed = self.__transpose_histogram()
        for day in range(7):
            for hour in range(24):
                hours.append(
                    sum(len(i.resolve_key(key))
                        for i in transposed.get(day, {}).get(hour, [])))
        return hours

    def __optimal_timeout_all(self, cid: str) -> float:
        flat_model = self.__model_builder.build()
        for day in self.__models[cid].values():
            for model in day.values():
                flat_model.extend(model)
        return flat_model.optimal_idle_timeout()

    def __optimal_timeout_timestamp(
            self, cid: str, day: int, hour: int) -> float:
        hist = self.__distribution_for_hour(cid, day, hour)
        if hist is None:
            return self.__optimal_timeout_all(cid)
        return hist.optimal_idle_timeout()

    # pylint: disable=invalid-name
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

    def __parse_trace(self) -> None:
        """Parses the json trace to generate all the histograms."""
        logger.debug('Parsing models.')
        with open(self.__trace_file) as trace:
            trace = json.load(trace)
            trace = [i for i in trace if i['PC'] != '_Total']
            key = operator.itemgetter('PC')
            self.__models = {}
            for pc, trace in itertools.groupby(sorted(trace, key=key), key=key):
                self.__servers.append(pc)
                self.__models[pc] = self.__parse_model(
                    {t['Type']: t['data'] for t in trace})
            if len(self.__servers) != len(set(self.__servers)):
                raise ValueError('There are duplicate PCs')
        self.__merge_histograms()
        self.__filter_out_empty_servers()

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
                model = self.__model_builder.build(
                    inactivity=dct['InactivityIntervals'],
                    activity=dct['ActivityIntervals'],
                    off_duration=dct['OffIntervals'],
                    off_fraction=dct['OffFrequencies'])
                if model.is_complete:
                    models.setdefault(day, {}).setdefault(
                        hour, model)
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
        if self.__do_merge:
            if not self.get_arg('per_hour'):
                self.__merge_per_hour()
            if not self.get_arg('per_pc'):
                self.__merge_per_pc()

    def __merge_per_hour(self) -> None:
        """Merge so all hours have the same model."""
        logger.debug('Merging histogram per hour.')
        merged = {}
        for cid, days in self.__models.items():
            merged_model = self.__model_builder.build()
            for day, hours in days.items():
                for hour, model in hours.items():
                    merged_model.extend(model)
            for day, hours in days.items():
                for hour in hours:
                    merged.setdefault(cid, {}).setdefault(
                        day, {}).setdefault(hour, merged_model)
        self.__models = merged

    def __merge_per_pc(self) -> None:
        """Merge so all PCs have the same model."""
        logger.debug('Merging histogram per PC.')
        merged = {}
        for cid, days in self.__models.items():
            for day, hours in days.items():
                for hour, model in hours.items():
                    merged.setdefault(day, {}).setdefault(
                        hour, self.__model_builder.build()).extend(model)
        for cid in self.__models:
            self.__models[cid] = merged

    def __filter_out_empty_servers(self) -> None:
        """Removes the servers that have no data in any of the histograms."""
        logger.debug('Filtering servers with no data.')
        empty_servers = set()
        for cid in self.__servers:
            if self.__is_empty_histogram(cid):
                empty_servers.add(cid)
                if cid in self.__models:
                    del self.__models[cid]
        self.__servers = sorted(set(self.__servers) - empty_servers)
        self.__empty_servers = sorted(empty_servers)
        logger.debug('%d servers have been filtered out.', len(empty_servers))

    def __is_empty_histogram(self, cid: str) -> bool:
        """Indicates if a histogram is empty."""
        for day in range(7):
            for hour in range(24):
                model = self.__get(cid, day, hour)
                if model is not None and model.is_complete:
                    return False
        return True

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
        """All the data of this object is loaded from the config object."""
        super(ActivityDistribution, self).__init__(
            do_merge=False, trace_file='trace_file')


@injector.singleton
class TrainingDistribution(ActivityDistributionBase):
    """Activity distribution for training purposes."""

    def __init__(self):
        """All the data of this object is loaded from the config object."""
        super(TrainingDistribution, self).__init__(
            do_merge=True, trace_file='training_file')


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
        elif training:
            return self.__training_distribution
        else:
            return self.__activity_distribution
