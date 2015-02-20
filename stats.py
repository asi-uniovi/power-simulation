"""Simulation statistics storage."""

import numpy
from activity_distribution import ActivityDistribution
from activity_distribution import HOUR
from activity_distribution import INV_DAYS
from activity_distribution import WEEK
from singleton import Singleton


class Stats(dict, metaclass=Singleton):
    """This is just a singleton dict with some helpers."""

    def __init__(self, config, env):
        super(Stats, self).__init__()
        self._activity_distribution = (
            ActivityDistribution.load_activity_distribution(config, env))

    def increment(self, key, inc=1):
        """Increments by inc a key. Creates the key if not existing."""
        self[key] = self.get(key, 0) + inc

    def append(self, key, value):
        """Append a new value to a list statistic. Create if non existing."""
        item = self.get(key, [])
        item.append(value)
        self[key] = item

    def add_to_bin(self, key, value, env):
        """Add a value to statistic binned by time."""
        hour = (env.now % WEEK(1)) // HOUR(1)
        self.setdefault(key, {}).setdefault(hour, []).append(value)

    def dump_histogram_to_file(self, key, filename):
        with open(filename, 'w') as f:
            f.write('i;n;Day;Hour;{0}\n'.format(key))
            for timestamp, data in self[key].items():
                day, hour = timestamp // 24, timestamp % 24
                f.write('{0}\n'.format(
                    ';'.join(str(x) for x in (
                        int(timestamp),
                        len(data),
                        INV_DAYS[day],
                        int(hour),
                        numpy.average(data),
                        self._activity_distribution.avg_inactivity_for_hour(
                            day, hour)))))
        with open('distribution-' + filename, 'w') as f:
            f.write('Day;Hour;Interval length;Frequency\n')
            for timestamp, data in self[key].items():
                day, hour = timestamp // 24, timestamp % 24
                f.write('{0}\n'.format(
                    ';'.join(str(x) for x in (
                        INV_DAYS[day],
                        int(hour),
                        ';'.join(str(i) for i in data)))))

    def __getitem__(self, key):
        try:
            return super(Stats, self).__getitem__(key)
        except KeyError:
            return 0
