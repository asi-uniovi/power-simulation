"""User (in)activity distribution parsing, fitting and generation."""

import collections
import csv
import functools
import json
import logging
import math
import numpy

import injector

from base import Base
from distribution import BernoulliDistribution
from distribution import DiscreteUniformDistribution
from distribution import EmpiricalDistribution
from distribution import NullDistribution
from static import HOUR, DAY, DAYS, WEEK

logger = logging.getLogger(__name__)


def timestamp_to_day(timestamp):
    """Converts from a simulation timestamp to the pair (day, hour)."""
    day = (timestamp % WEEK(1)) // DAY(1)
    hour = (timestamp % DAY(1)) // HOUR(1)
    assert 0 <= day <= 6
    assert 0 <= hour <= 23
    return int(day), int(hour)


def _distribution_for_hour(histogram, day, hour):
    """Queries the activity distribution to the get average inactivity."""
    return histogram.get(day, {}).get(hour)


def _flatten_histogram(histogram):
    """Makes a histogram be a list of 168 elements."""
    if histogram is None:
        return []

    # TODO: use distributions.NullDistrbution for this.
    null = collections.namedtuple('null', ['mean', 'median', 'sample_size'])
    ret = []
    for day in range(7):
        for hour in range(24):
            ret.append(histogram.get(day, {}).get(hour, null(mean=0,
                                                             median=0,
                                                             sample_size=0)))
    assert len(ret) == 168, len(ret)
    return ret


@injector.singleton
class ActivityDistribution(Base):
    """Stores the hourly activity distribution over a week.

    Each bucket of the histogram contains the distribution of the log file
    processed. Each bucket represents one hour of the week.
    """

    def __init__(self):
        """All the data of this object is loaded from the config object."""
        super(ActivityDistribution, self).__init__()
        activity = functools.partial(
            self.get_config, section='activity_distribution')
        inactivity = functools.partial(
            self.get_config, section='inactivity_distribution')
        shutdown = functools.partial(
            self.get_config, section='shutdown_distribution')
        self._xmin = float(inactivity('xmin'))
        self._xmax = float(inactivity('xmax'))
        self._noise_threshold = float(inactivity('noise_threshold'))

        if self.simulating_per_pc:
            self._inactivity_intervals_histogram = self.__load_and_fit2(
                inactivity('per_pc_file'), do_filter=True)
        else:
            self._inactivity_intervals_histogram = self.__load_and_fit(
                inactivity('intervals_file'), do_filter=True)

        self._activity_intervals_histogram = self.__load_and_fit(
            activity('intervals_file'))
        self._off_intervals_histogram = self.__load_and_fit(
            shutdown('intervals_file'), do_filter=True)
        self._off_probability_histogram = self.__load_and_fit(
            shutdown('probability_file'), BernoulliDistribution)

    @property
    def servers(self):
        if self.simulating_per_pc:
            return self._servers
        return self.get_config_int('servers')

    def random_activity_for_hour(self, day, hour):
        """Queries the activity distribution and generates a random sample."""
        distribution = _distribution_for_hour(
            self._activity_intervals_histogram, day, hour)
        if distribution is not None:
            rnd_activity = distribution.rvs()
            while math.isnan(rnd_activity):
                rnd_activity = distribution.rvs()
            return rnd_activity

        raise RuntimeError('Distribution undefined for {} {}'.format(day, hour))

    def random_activity_for_timestamp(self, timestamp):
        """Queries the activity distribution and generates a random sample."""
        return self.random_activity_for_hour(*timestamp_to_day(timestamp))

    def random_inactivity_for_hour(self, cid, day, hour):
        """Queries the activity distribution and generates a random sample."""
        hist = self._get_histogram(self._inactivity_intervals_histogram, cid)
        distribution = _distribution_for_hour(hist, day, hour)
        if distribution is not None:
            rnd_inactivity = distribution.rvs()
            if self._noise_threshold is not None:
                while (rnd_inactivity > self._noise_threshold
                       or math.isnan(rnd_inactivity)):
                    rnd_inactivity = distribution.rvs()
            return rnd_inactivity

        raise RuntimeError('Distribution undefined for {} {}'.format(day, hour))

    def random_inactivity_for_timestamp(self, cid, timestamp):
        """Queries the activity distribution and generates a random sample."""
        return self.random_inactivity_for_hour(
            cid, *timestamp_to_day(timestamp))

    def shutdown_for_hour(self, day, hour):
        """Determines whether a computer should turndown or not."""
        distribution = _distribution_for_hour(
            self._off_probability_histogram, day, hour)
        if distribution is not None:
            return distribution.mean
        return 0.0

    def shutdown_for_timestamp(self, timestamp):
        """Determines whether a computer should turndown or not."""
        return self.shutdown_for_hour(*timestamp_to_day(timestamp))

    def off_interval_for_hour(self, day, hour):
        """Samples an off interval for the day and hour provided"""
        distribution = _distribution_for_hour(
            self._off_intervals_histogram, day, hour)
        if distribution is not None:
            off_interval = distribution.rvs()
            while off_interval < 0:
                off_interval = distribution.rvs()
            return off_interval
        return 0.0

    def off_interval_for_timestamp(self, timestamp):
        """Samples an off interval for the day and hour provided"""
        return self.off_interval_for_hour(*timestamp_to_day(timestamp))

    def get_all_hourly_summaries(self, key, summaries=('mean', 'median')):
        """Returns the summaries per hour."""
        if isinstance(self._resolve_histogram(key), list):
            return [{s: getattr(i, s) for s in summaries}
                    for i in _flatten_histogram(self._resolve_histogram(key)[0])]
        return [{s: getattr(i, s) for s in summaries}
                for i in _flatten_histogram(self._resolve_histogram(key))]

    def get_all_hourly_count(self, key):
        """Returns the count of items per hourly subhistogram."""
        if isinstance(self._resolve_histogram(key), list):
            return [i.sample_size
                    for h in self._resolve_histogram(key)
                    for i in _flatten_histogram(h)]
        return [i.sample_size
                for i in _flatten_histogram(self._resolve_histogram(key))]

    @functools.lru_cache()
    def optimal_idle_timeout(self, cid):
        """Calculates the value of the idle timer for a given satisfaction."""
        hist = sorted(self._flatten_all_histogram(
            self._get_histogram(self._inactivity_intervals_histogram, cid)))
        if len(hist) == 0:
            return self.get_config_int('default_timeout')
        return hist[int(
            self.get_config_int('target_satisfaction') * len(hist) / 100)]

    @functools.lru_cache()
    def global_idle_timeout(self):
        """Calculates the value of the idle timer for a given satisfaction."""
        hist = sorted(self._flatten_all_histogram(
            self._inactivity_intervals_histogram))
        return hist[int(
            self.get_config_int('target_satisfaction') * len(hist) / 100)]

    def _resolve_histogram(self, key):
        """Matches histograms and keys."""
        if key == 'ACTIVITY_TIME':
            return self._activity_intervals_histogram
        elif key == 'INACTIVITY_TIME':
            return self._inactivity_intervals_histogram
        elif key == 'USER_SHUTDOWN_TIME':
            return self._off_intervals_histogram
        elif key == 'AUTO_SHUTDOWN_TIME':
            return None
        elif key == 'IDLE_TIME':
            return None
        raise KeyError('Invalid key for histogram.')

    def _get_histogram(self, hist, cid):
        """Resolves histogram on a per PC world."""
        if self.simulating_per_pc:
            return hist[cid]
        return hist

    def _flatten_all_histogram(self, hist):
        """Makes a histogram completely flat."""
        if isinstance(hist, list):
            return [d for pc in hist for h in pc.values() for i in h.values()
                    for d in i.data]
        return [d for h in hist.values() for i in h.values() for d in i.data]

    def __load_and_fit(self, filename, distr=None, do_filter=False):
        """Parses the CSV with the trace formatted {day, hour, inactivity+}."""
        logger.info('Parsing and fitting distributions.')
        with open(filename) as trace:
            try:
                histogram = {}
                reader = csv.reader(trace, delimiter=';')
                next(reader, None)
                for item in reader:
                    day = DAYS[item[0]]
                    hour = int(item[1])
                    data = [float(j) for j in item[2:]]
                    if do_filter:
                        data = [i for i in data
                                if self._xmin <= i <= self._xmax]
                    data = numpy.asarray(data)
                    if len(data) == 0:
                        continue
                    fdistr = distr
                    if fdistr is None:
                        if len(data) > 1:
                            fdistr = EmpiricalDistribution
                        elif len(data) == 1:
                            fdistr = DiscreteUniformDistribution
                        else:
                            raise RuntimeError('Cannot fit non-intervals.')
                    histogram.setdefault(day, {})[hour] = fdistr(*data)
                    logger.debug('Fitted distribution for %s %s', day, hour)
                return histogram
            except csv.Error as error:
                raise RuntimeError(('Error reading {}:{}: {}'
                                    .format(filename, trace.line_num, error)))

    def __load_and_fit2(self, filename, distr=None, do_filter=False):
        """Parses the JSON with the trace per PC. Experimental."""
        logger.info('Parsing and fitting per PC distributions.')
        with open(filename) as raw_trace:
            trace = json.load(raw_trace)
            self._servers = len(trace)
            histograms = []
            for pc in trace:
                histogram = {}
                for item in pc['data']:
                    day = DAYS[item['Day']]
                    hour = int(item['Hour'])
                    data = [float(j) for j in item['Intervals']]
                    if do_filter:
                        data = [i for i in data
                                if self._xmin <= i <= self._xmax]
                    data = numpy.asarray(data)
                    fdistr = distr
                    if fdistr is None:
                        if len(data) > 1:
                            fdistr = EmpiricalDistribution
                        elif len(data) == 1:
                            fdistr = DiscreteUniformDistribution
                        else:
                            fdistr = NullDistribution
                    histogram.setdefault(day, {})[hour] = fdistr(*data)
                    logger.debug('Fitted distribution for %s %s', day, hour)
                histograms.append(histogram)
            return histograms
