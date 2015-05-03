"""User (in)activity distribution parsing, fitting and generation."""

import csv
import functools
import injector
import numpy
import logging
import scipy.stats

from base import Base
from static import HOUR, DAY, DAYS, WEEK

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


DISTRIBUTIONS = {
    'exponential': scipy.stats.expon,  # pylint: disable=no-member
    'lognormal': scipy.stats.lognorm,  # pylint: disable=no-member
    'pareto': scipy.stats.pareto,  # pylint: disable=no-member
}


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
        getter = functools.partial(
            self.get_config, section='activity_distribution')
        self._histogram = {}
        self._distribution = DISTRIBUTIONS[getter('distribution')]
        self._xmin = float(getter('xmin'))
        self._xmax = float(getter('xmax'))
        self._noise_threshold = float(getter('noise_threshold'))
        self.__load_raw_trace_and_fit(getter('filename'))

    def random_inactivity_for_hour(self, day, hour):
        """Queries the activity distribution and generates a random sample."""
        distribution = self._distribution_for_hour(day, hour)
        if distribution is not None:
            rnd_inactivity = distribution.resample(size=1)[0][0]
            if self._noise_threshold is not None:
                while rnd_inactivity > self._noise_threshold:
                    rnd_inactivity = distribution.resample(size=1)[0][0]
            return rnd_inactivity

        raise RuntimeError('Distribution undefined for {} {}'.format(day, hour))

    def random_inactivity_for_timestamp(self, timestamp):
        """Queries the activity distribution and generates a random sample."""
        return self.random_inactivity_for_hour(*timestamp_to_day(timestamp))

    def _distribution_for_hour(self, day, hour):
        """Queries the activity distribution to the get average inactivity."""
        return self._histogram[day][hour]

    def _bandwidth(self, data):
        """Silverman's rule of thumb for bandwith estimation."""
        # return 1.06 * numpy.std(data) * numpy.power(len(data), -1/5)
        return 0.00005

    def __load_raw_trace_and_fit(self, filename):
        """Parses the CSV with the trace formatted {day, hour, inactivity+}."""
        logger.info('Parsing and fitting distributions.')
        with open(filename) as trace:
            try:
                reader = csv.reader(trace, delimiter=';')
                next(reader, None)
                for item in reader:
                    day = DAYS[item[0]]
                    hour = int(item[1])
                    # pylint: disable=no-member
                    s = numpy.asarray(
                        [i for i in [float(j) for j in item[2:]]
                         if self._xmin <= i <= self._xmax])
                    self._histogram.setdefault(day, {})[hour] = (
                        scipy.stats.gaussian_kde(s, self._bandwidth(s)))
                    logger.debug('Fitted distribution for %s %s', day, hour)
            except csv.Error as error:
                raise RuntimeError(('Error reading {}:{}: {}'
                                    .format(filename, trace.line_num, error)))
