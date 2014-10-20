"""User activiy distribution parsing and managing."""

import csv
import numpy
from collections import defaultdict

DAYS = {
    'Sunday': 0,
    'Monday': 1,
    'Tuesday': 2,
    'Wednesday': 3,
    'Thursday': 4,
    'Friday': 5,
    'Saturday': 6,
}

DISTRIBUTIONS = {
    'exp': numpy.random.exponential,
}


HOUR = lambda x: x * 60 * 60
DAY = lambda x: x * HOUR(24)
WEEK = lambda x: x * DAY(7)


def float_es(string):
    """Parse a Spanish float from string (converting the ,)."""
    return float(string.replace(',', '.'))


class ActivityDistribution(object):
    """Stores the hourly activity distribution over a week.

    Each bucket of the histogram contains the average duration of the inactivity
    intervals that start on each hour.
    """

    def __init__(self, filename, distribution):
        self._histogram = defaultdict(lambda: defaultdict(float))
        self._distribution = DISTRIBUTIONS[distribution]
        self.__load_trace(filename)

    def avg_inactivity_for_hour(self, day, hour):
        """Queries the activity distribution to the get average inactivity."""
        return self._histogram[day][hour]

    def random_inactivity_for_hour(self, day, hour):
        """Queries the activity distribution and generates a random sample."""
        if self._distribution:
            return self._distribution(self.avg_inactivity_for_hour(hour, day))
        raise RuntimeError('Distribution is not defined for this model')

    def random_inactivity_for_timestamp(self, timestamp):
        """Queries the activity distribution and generates a random sample."""
        day, hour = self._timestamp_to_day(timestamp)
        return self.random_inactivity_for_hour(day, hour)

    def _timestamp_to_day(self, timestamp):
        day, hours = divmod(timestamp % WEEK(1), DAY(1))
        assert 0 <= day <= 6, 'Invalid day index yielded'
        assert 0 <= hours // HOUR(1) <= 23, 'Invalid hour index yielded'
        return day, hours // HOUR(1)

    def __load_trace(self, filename):
        """Parses the CSV with the trace formatted {day, hour, inactivity}."""
        with open(filename, newline='', encoding='utf-8') as trace:
            try:
                dialect = csv.Sniffer().sniff(trace.read(1024))
                trace.seek(0)
                reader = csv.reader(trace, dialect)

                next(reader)
                for day, hour, inactivity in reader:
                    self._histogram[DAYS[day]][int(hour)] = float_es(inactivity)
            except csv.Error as error:
                raise RuntimeError(('Error reading {}:{}: {}'
                                    .format(filename, trace.line_num, error)))
