"""User activiy distribution parsing and managing."""

import csv
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


def float_es(string):
    """Parse a Spanish float from string (converting the ,)."""
    return float(string.replace(',', '.'))


class ActivityDistribution(object):
    """Stores the hourly activity distribution over a week.

    Each bucket of the histogram contains the average duration of the inactivity
    intervals that start on each hour.
    """

    def __init__(self, filename, distribution=None):
        self._histogram = defaultdict(lambda: defaultdict(float))
        self._distribution = distribution
        self.__load_trace(filename)

    def avg_inactivity_for_hour(self, day, hour):
        """Queries the activity distribution to the get average inactivity."""
        return self._histogram[day][hour]

    def random_inactivity_for_hour(self, day, hour):
        """Queries the activity distribution and generates a random sample."""
        if self._distribution:
            return self._distribution(self.avg_inactivity_for_hour(hour, day))
        raise RuntimeError('Distribution is not defined for this model')

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
