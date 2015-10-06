"""User (in)activity distribution parsing, fitting and generation."""

import csv
import functools
import injector
import math
import numpy
import logging

from base import Base
from distribution import BernoulliDistribution
from distribution import DiscreteUniformDistribution
from distribution import EmpiricalDistribution
from static import HOUR, DAY, DAYS, WEEK

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def float_es(string):
    """Parse a Spanish float from string (converting the ,)."""
    return float(string.replace(',', '.'))


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
    return [i for h in histogram.values() for i in h.values()]


@injector.singleton
class ActivityDistribution(Base):
    """Stores the hourly activity distribution over a week.

    Each bucket of the histogram contains the distribution of the log file
    processed. Each bucket represents one hour of the week.
    """

    def __init__(self):
        """All the data of this object is loaded from the config object."""
        super(ActivityDistribution, self).__init__()
        inactivity = functools.partial(
            self.get_config, section='inactivity_distribution')
        shutdown = functools.partial(
            self.get_config, section='shutdown_distribution')
        self._xmin = float(inactivity('xmin'))
        self._xmax = float(inactivity('xmax'))
        self._noise_threshold = float(inactivity('noise_threshold'))
        self._inactivity_intervals_histogram = self.__load_and_fit(
            inactivity('intervals_file'), do_filter=True)
        self._off_intervals_histogram = self.__load_and_fit(
            shutdown('intervals_file'), do_filter=True)
        self._off_probability_histogram = self.__load_and_fit(
            shutdown('probability_file'), BernoulliDistribution)

    def random_inactivity_for_hour(self, day, hour):
        """Queries the activity distribution and generates a random sample."""
        distribution = _distribution_for_hour(
            self._inactivity_intervals_histogram, day, hour)
        if distribution is not None:
            rnd_inactivity = distribution.rvs()
            if self._noise_threshold is not None:
                while (rnd_inactivity > self._noise_threshold
                       or math.isnan(rnd_inactivity)):
                    rnd_inactivity = distribution.rvs()
            return rnd_inactivity

        raise RuntimeError('Distribution undefined for {} {}'.format(day, hour))

    def random_inactivity_for_timestamp(self, timestamp):
        """Queries the activity distribution and generates a random sample."""
        return self.random_inactivity_for_hour(*timestamp_to_day(timestamp))

    def inactivity_means(self):
        """Calculates the mean of the inactivity distribution per hour."""
        return [i.mean for i in _flatten_histogram(
            self._inactivity_intervals_histogram)]

    def inactivity_medians(self):
        """Calculates the median of the inactivity distribution per hour."""
        return [i.median for i in _flatten_histogram(
            self._inactivity_intervals_histogram)]

    def inactivity_counts(self):
        """Calculates the counts of the inactivity distribution per hour."""
        return [i.sample_size for i in _flatten_histogram(
            self._inactivity_intervals_histogram)]

    def shutdown_counts(self):
        """Calculates the counts of the shutdown distribution per hour."""
        return [i.sample_size for i in _flatten_histogram(
            self._off_intervals_histogram)]

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
                    # pylint: disable=no-member,invalid-name
                    s = [float(j) for j in item[2:]]
                    if do_filter:
                        s = [i for i in s if self._xmin <= i <= self._xmax]
                    s = numpy.asarray(s)
                    if len(s) == 0:
                        continue
                    if distr is None:
                        if len(s) > 1:
                            distr = EmpiricalDistribution
                        elif len(s) == 1:
                            distr = DiscreteUniformDistribution
                    histogram.setdefault(day, {})[hour] = distr(*s)
                    logger.debug('Fitted distribution for %s %s', day, hour)
                return histogram
            except csv.Error as error:
                raise RuntimeError(('Error reading {}:{}: {}'
                                    .format(filename, trace.line_num, error)))
