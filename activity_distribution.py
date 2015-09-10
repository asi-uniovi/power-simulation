"""User (in)activity distribution parsing, fitting and generation."""

import csv
import functools
import injector
import math
import numpy
import logging

from base import Base
from distribution import EmpiricalDistribution, BernoulliDistribution
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
        inactivity = functools.partial(
            self.get_config, section='inactivity_distribution')
        shutdown = functools.partial(
            self.get_config, section='shutdown_distribution')
        self._xmin = float(inactivity('xmin'))
        self._xmax = float(inactivity('xmax'))
        self._noise_threshold = float(inactivity('noise_threshold'))
        self._inactivity_intervals_histogram = self.__load_and_fit(
            inactivity('intervals_file'))
        self._off_intervals_histogram = self.__load_and_fit(
            shutdown('intervals_file'))
        self._off_probability_histogram = self.__load_and_fit(
            shutdown('probability_file'))

    def random_inactivity_for_hour(self, day, hour):
        """Queries the activity distribution and generates a random sample."""
        distribution = self._distribution_for_hour(day, hour)
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

    def _distribution_for_hour(self, day, hour):
        """Queries the activity distribution to the get average inactivity."""
        return self._inactivity_intervals_histogram[day][hour]

    def __load_and_fit(self, filename):
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
                    # pylint: disable=no-member
                    s = numpy.asarray(
                        [i for i in [float(j) for j in item[2:]]
                         if self._xmin <= i <= self._xmax])
                    if len(s) > 1:
                        distr = EmpiricalDistribution(s)
                    elif len(s) == 1:
                        distr = BernoulliDistribution(s[0])
                    elif len(s) == 0:
                        distr = BernoulliDistribution(0)
                    histogram.setdefault(day, {})[hour] = distr
                    logger.debug('Fitted distribution for %s %s', day, hour)
                return histogram
            except csv.Error as error:
                raise RuntimeError(('Error reading {}:{}: {}'
                                    .format(filename, trace.line_num, error)))
