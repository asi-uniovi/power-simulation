"""User (in)activity distribution parsing, fitting and generation."""

import functools
import json
import logging
import numpy

import injector

from base import Base
from distribution import DiscreteUniformDistribution
from distribution import EmpiricalDistribution
from static import HOUR, DAY, DAYS, WEEK

logger = logging.getLogger(__name__)


def timestamp_to_day(timestamp):
    """Converts from a simulation timestamp to the pair (day, hour)."""
    day = int((timestamp % WEEK(1)) // DAY(1))
    hour = int((timestamp % DAY(1)) // HOUR(1))
    assert 0 <= day <= 6, day
    assert 0 <= hour <= 23, hour
    return day, hour


def previous_hour(day, hour):
    """Gets the previous hour with wrap."""
    hour -= 1
    if hour < 0:
        hour = 23
        day -= 1
        if day < 0:
            day = 6
    assert 0 <= day <= 6, day
    assert 0 <= hour <= 23, hour
    return day, hour


@injector.singleton
class ActivityDistribution(Base):
    """Stores the hourly activity distribution over a week.

    Each bucket of the histogram contains the distribution of the log file
    processed. Each bucket represents one hour of the week.
    """

    def __init__(self):
        """All the data of this object is loaded from the config object."""
        super(ActivityDistribution, self).__init__()
        self.__default_timeout = self.get_config_int('default_timeout')
        self.__target_satisfaction = self.get_config_int('target_satisfaction')
        self.__noise_threshold = self.get_config_float(
            'noise_threshold', section='trace')
        self.__xmin = self.get_config_float('xmin', section='trace')
        self.__xmax = self.get_config_float('xmax', section='trace')
        assert 0 < self.__noise_threshold > self.__xmin
        assert 0 < self.__xmin < self.__xmax
        self.__servers = []
        self.__inactivity_intervals_histograms = {}
        self.__activity_intervals_histograms = {}
        self.__off_intervals_histograms = {}
        self.__off_fractions_histograms = {}
        self.__parse_trace(self.get_config('trace_file', section='trace'))

    @property
    def servers(self):
        """Read only servers list."""
        return self.__servers

    def random_activity_for_hour(self, cid, day, hour):
        """Queries the activity distribution and generates a random sample."""
        return self.__draw_from_distribution(
            self.__distribution_for_hour(
                self.__activity_intervals_histograms, cid, day, hour),
            min_value=0.1, max_value=self.__xmax)

    def random_activity_for_timestamp(self, cid, timestamp):
        """Queries the activity distribution and generates a random sample."""
        return self.random_activity_for_hour(cid, *timestamp_to_day(timestamp))

    def random_inactivity_for_hour(self, cid, day, hour):
        """Queries the activity distribution and generates a random sample."""
        distribution = self.__distribution_for_hour(
            self.__inactivity_intervals_histograms, cid, day, hour)
        rnd_inactivity = self.__draw_from_distribution(
            distribution, min_value=self.__xmin, max_value=self.__xmax)
        if self.__noise_threshold is not None:
            while rnd_inactivity > self.__noise_threshold:
                rnd_inactivity = self.__draw_from_distribution(
                    distribution, min_value=self.__xmin, max_value=self.__xmax)
        return rnd_inactivity

    def random_inactivity_for_timestamp(self, cid, timestamp):
        """Queries the activity distribution and generates a random sample."""
        return self.random_inactivity_for_hour(
            cid, *timestamp_to_day(timestamp))

    def off_fraction_for_hour(self, cid, day, hour):
        """Determines whether a computer should turndown or not."""
        return self.__draw_from_distribution(
            self.__distribution_for_hour(
                self.__off_fractions_histograms, cid, day, hour))

    def off_fraction_for_timestamp(self, cid, timestamp):
        """Determines whether a computer should turndown or not."""
        return self.off_fraction_for_hour(cid, *timestamp_to_day(timestamp))

    def off_interval_for_hour(self, cid, day, hour):
        """Samples an off interval for the day and hour provided"""
        return self.__draw_from_distribution(
            self.__distribution_for_hour(
                self.__off_intervals_histograms, cid, day, hour),
            min_value=self.__xmin, max_value=self.__xmax)

    def off_interval_for_timestamp(self, cid, timestamp):
        """Samples an off interval for the day and hour provided"""
        return self.off_interval_for_hour(cid, *timestamp_to_day(timestamp))

    @functools.lru_cache()
    def optimal_idle_timeout(self, cid):
        """Calculates the value of the idle timer for a given satisfaction."""
        hist = sorted(self.__flatten_histogram(
            self.__inactivity_intervals_histograms, cid))
        if len(hist) == 0:
            return self.__default_timeout
        timeout = hist[int(self.__target_satisfaction * len(hist) / 100)]
        if timeout < self.__default_timeout:
            logger.debug('timeout smaller than default timeout for %s', cid)
            return self.__default_timeout
        return timeout

    def global_idle_timeout(self):
        """Calculates the value of the idle timer for a given satisfaction."""
        return numpy.mean(
            [self.optimal_idle_timeout(cid) for cid in self.__servers])

    def get_all_hourly_summaries(self, key, summaries=('mean', 'median')):
        """Returns the summaries per hour."""
        return [{s: getattr(numpy, s)([getattr(i, s) for i in values])
                 for s in summaries}
                for day in self.__transpose_histogram(
                    self.__resolve_histogram(key)).values()
                for values in day.values()]

    def get_all_hourly_count(self, key):
        """Returns the counts per hour."""
        return [sum(i.sample_size for i in values)
                for day in self.__transpose_histogram(
                    self.__resolve_histogram(key)).values()
                for values in day.values()]

    def __resolve_histogram(self, key):
        """Matches histograms and keys."""
        if key == 'ACTIVITY_TIME':
            return self.__activity_intervals_histograms
        elif key == 'INACTIVITY_TIME':
            return self.__inactivity_intervals_histograms
        elif key == 'USER_SHUTDOWN_TIME':
            return self.__off_intervals_histograms
        elif key == 'AUTO_SHUTDOWN_TIME':
            return None
        elif key == 'IDLE_TIME':
            return None
        raise KeyError('Invalid key for histogram.')

    def __transpose_histogram(self, histogram):
        """Converts the {PC: {Day: {Hour: x}}} hist to {Day: {Hour: [x*]}}."""
        transposed = {}
        if histogram is not None:
            for day in range(7):
                for hour in range(24):
                    for value in histogram.values():
                        if value.get(day, {}).get(hour) is not None:
                            transposed.setdefault(day, {}).setdefault(
                                hour, []).append(value.get(day, {}).get(hour))
        return transposed

    def __flatten_histogram(self, histogram, cid):
        """Makes a histogram completely flat."""
        return [i for day in histogram[cid].values()
                for hour in day.values() if hour is not None for i in hour.data]

    def __distribution_for_hour(self, histogram, cid, day, hour):
        """Queries the activity distribution to the get average inactivity."""
        previous_count = 0
        distribution = self.__get(histogram, cid, day, hour)
        while distribution is None:
            if previous_count > 168:
                return None
            previous_count += 1
            day, hour = previous_hour(day, hour)
            distribution = self.__get(histogram, cid, day, hour)
        return distribution

    def __get(self, histogram, cid, day, hour):
        """Generic getter for a histogram."""
        return histogram.get(cid, {}).get(day, {}).get(hour)

    def __draw_from_distribution(self, distribution, min_value=0,
                                 max_value=float('inf')):
        """Gets a value from a distribution bounding the limit."""
        if distribution is None:
            return min_value
        rnd = distribution.rvs()
        while min_value >= rnd >= max_value:
            rnd = distribution.rvs()
        return rnd

    def __parse_trace(self, trace_path):
        """Parses the json trace to generate all the histograms."""
        with open(trace_path) as trace:
            trace = json.load(trace)
            trace = [i for i in trace if i['PC'] != '_Total']
            self.__parse_servers(trace)
            self.__parse_inactivity_intervals(trace)
            self.__parse_activity_intervals(trace)
            self.__parse_off_intervals(trace)
            self.__parse_off_fractions(trace)
            self.__filter_out_empty_servers()

    def __parse_servers(self, trace):
        """Gets and validates the server hostnames from the trace."""
        logger.info('Parsing and validating server hostnames.')
        # TODO(m3drano): This should check for repeated hostnames too.
        pcs = [set(i['PC'] for i in trace if i['Type'] == key)
               for key in set(j['Type'] for j in trace)]
        if len(set(len(i) for i in pcs)) != 1:
            raise ValueError('PC names are not consistent across keys')
        self.__servers = sorted(pcs.pop())

    def __parse_inactivity_intervals(self, trace):
        """Loads the inactivity intervals from the trace."""
        logger.info('Parsing inactivity intervals.')
        self.__inactivity_intervals_histograms = self.__parse_histograms(
            trace, 'InactivityIntervals', do_filter=True)

    def __parse_activity_intervals(self, trace):
        """Process the activity intervals."""
        logger.info('Parsing activity intervals.')
        self.__activity_intervals_histograms = self.__parse_histograms(
            trace, 'ActivityIntervals')

    def __parse_off_intervals(self, trace):
        """Process the off intervals."""
        logger.info('Parsing off intervals.')
        self.__off_intervals_histograms = self.__parse_histograms(
            trace, 'OffIntervals')

    def __parse_off_fractions(self, trace):
        """Process the off fractions."""
        logger.info('Parsing off fractions.')
        self.__off_fractions_histograms = self.__parse_histograms(
            trace, 'OffFrequencies', do_reduce=False)

    def __filter_out_empty_servers(self):
        """Removes the servers that have no data in any of the histograms."""
        logger.info('Filtering servers with no data.')
        empty_servers = set()
        for cid in self.__servers:
            if (self.__is_empty_histogram(
                    self.__inactivity_intervals_histograms, cid)
                    or self.__is_empty_histogram(
                        self.__activity_intervals_histograms, cid)
                    or self.__is_empty_histogram(
                        self.__off_intervals_histograms, cid)
                    or self.__is_empty_histogram(
                        self.__off_fractions_histograms, cid)):
                empty_servers.add(cid)
        self.__servers = sorted(set(self.__servers) - empty_servers)
        logger.info('%d servers have been filtered out.', len(empty_servers))

    def __is_empty_histogram(self, histogram, cid):
        """Indicates if a histogram is empty."""
        for day in range(7):
            for hour in range(24):
                if self.__get(histogram, cid, day, hour) is not None:
                    return False
        return True

    def __parse_histograms(self, trace, hist_key, do_filter=False,
                           do_reduce=True):
        """Parses the histogram to get a {PC: hist} dict."""
        histograms = {i['PC']: self.__parse_histogram(i, do_filter, do_reduce)
                      for i in trace if i['Type'] == hist_key}
        if set(histograms.keys()) != set(self.__servers):
            raise ValueError('PCs on Key %s are not consistent' % hist_key)
        return histograms

    def __parse_histogram(self, trace, do_filter, do_reduce):
        """Generic parser of a histogram element."""
        if len(trace.get('data', [])) > 168:
            raise ValueError('The trace contains more than 168 objects')
        if len(trace.get('data', [])) < 168:
            logger.warning('The trace contains less than 168 objects')
        histogram = {}
        for d in trace['data']:
            day = DAYS[d['Day']]
            hour = int(d['Hour'])
            assert 0 <= day <= 6
            assert 0 <= hour <= 23
            histogram.setdefault(day, {})[hour] = self.__process(
                d['Intervals'], do_filter, do_reduce)
        return histogram

    def __process(self, data, do_filter, do_reduce):
        """Process one data unit."""
        sample_size = len(data)
        if do_filter:
            data = numpy.asarray([i for i in data
                                  if self.__xmin <= i <= self.__xmax])
        elif do_reduce:
            data = numpy.asarray([i for i in data if i > 0])
        else:
            data = numpy.asarray(data)
        if sample_size != len(data):
            logger.debug('process(): elements filtered out: %d -> %d',
                         sample_size, len(data))
        if len(set(data)) > 1:
            return EmpiricalDistribution(sample_size, *data)
        elif len(data) > 0:
            return DiscreteUniformDistribution(sample_size, *data)
        return None
