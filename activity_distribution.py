"""User activity distribution parsing and managing."""

import csv
import functools
import numpy
import logging
import scipy
import scipy.stats
from base import Base
from collections import defaultdict
from singleton import Singleton

logger = logging.getLogger(__name__)

DAYS = {
    'Sunday': 0,
    'Monday': 1,
    'Tuesday': 2,
    'Wednesday': 3,
    'Thursday': 4,
    'Friday': 5,
    'Saturday': 6,
}

INV_DAYS = {v: k for k, v in DAYS.items()}

DISTRIBUTIONS = {
    'exp': numpy.random.exponential,
    'par': numpy.random.pareto,
}


HOUR = lambda x: x * 60 * 60
DAY = lambda x: x * HOUR(24)
WEEK = lambda x: x * DAY(7)


def float_es(string):
    """Parse a Spanish float from string (converting the ,)."""
    assert type(string) == type('')
    return float(string.replace(',', '.'))


class ActivityDistribution(Base, metaclass=Singleton):
    """Stores the hourly activity distribution over a week.

    Each bucket of the histogram contains the average duration of the inactivity
    intervals that start on each hour.
    """

    def __init__(self, config, filename, distribution, env):
        super(ActivityDistribution, self).__init__(config)
        self._histogram = defaultdict(lambda: defaultdict(float))
        self._distribution = DISTRIBUTIONS[distribution]
        self._env = env
        self.__load_raw_trace_and_fit(filename)

    def avg_inactivity_for_hour(self, day, hour):
        """Queries the activity distribution to the get average inactivity."""
        return self._histogram[day][hour]

    def random_inactivity_for_hour(self, day, hour):
        """Queries the activity distribution and generates a random sample."""
        inactivity = self.avg_inactivity_for_hour(day, hour)
        if callable(inactivity):
            return inactivity()
        if self._distribution:
            return self._distribution(inactivity)
        raise RuntimeError('Distribution is not defined for this model')

    def random_inactivity_for_timestamp(self, timestamp):
        """Queries the activity distribution and generates a random sample."""
        day, hour = self._timestamp_to_day(timestamp)
        return self.random_inactivity_for_hour(day, hour)

    def _timestamp_to_day(self, timestamp):
        day = (timestamp % WEEK(1)) // DAY(1)
        hour = (timestamp % DAY(1)) // HOUR(1)
        assert 0 <= day <= 6, day
        assert 0 <= hour <= 23, hour
        return day, hour

    def __load_trace(self, filename):
        """Parses the CSV with the trace formatted {day, hour, inactivity}."""
        with open(filename) as trace:
            try:
                dialect = csv.Sniffer().sniff(trace.read(1024))
                trace.seek(0)
                reader = csv.reader(trace, dialect)

                next(reader)
                data = []  # Max 168 values (hours of a week).
                for day, hour, inactivity in reader:
                    inactivity = float_es(inactivity)
                    data.append(inactivity)
                    assert self._histogram.get(DAYS[day], {}).get(int(hour)) is None
                    self._histogram[DAYS[day]][int(hour)] = inactivity

                logger.info('Distr.: avg(%.2f), std(%.2f), [%.2f; %.2f]',
                            numpy.average(data), numpy.std(data),
                            numpy.min(data), numpy.max(data))
            except csv.Error as error:
                raise RuntimeError(('Error reading {}:{}: {}'
                                    .format(filename, trace.line_num, error)))

    def __load_raw_trace_and_fit(self, filename):
        """Parses the CSV with the trace formatted {day, hour, inactivity*}."""
        with open(filename) as trace:
            try:
                dialect = csv.Sniffer().sniff(trace.read(1024))
                trace.seek(0)
                reader = csv.reader(trace, dialect)

                next(reader)
                for item in reader:
                    day = item[0]
                    hour = item[1]
                    shape, scale, loc = scipy.stats.pareto.fit(
                        numpy.asarray(list(map(float, item[2:]))))
                    self._histogram[DAYS[day]][int(hour)] = (
                        functools.partial(lambda s, l: (numpy.random.pareto(s) + 1) * l,
                                          shape, loc))

                    logger.info(
                        'Distribution fitted to pareto of shape = %f loc = %f', shape, loc)
            except csv.Error as error:
                raise RuntimeError(('Error reading {}:{}: {}'
                                    .format(filename, trace.line_num, error)))

    @classmethod
    def load_activity_distribution(cls, config, env):
        return cls(config,
                   filename=config.get('activity_distribution',
                                       'filename'),
                   distribution=config.get('activity_distribution',
                                           'distribution'),
                   env=env)
