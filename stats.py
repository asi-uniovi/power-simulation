"""Simulation statistics storage."""

import injector

from activity_distribution import ActivityDistribution
from base import env_key
from static import HOUR, INV_DAYS, WEEK


@injector.singleton
class Stats(dict):
    """This is just a singleton dict with some helpers."""

    @injector.inject(activity_distribution=ActivityDistribution, env=env_key)
    def __init__(self, activity_distribution, env):
        super(Stats, self).__init__()
        self._activity_distribution = activity_distribution
        self._env = env

    def increment(self, key, inc=1):
        """Increments by inc a key. Creates the key if not existing."""
        self[key] = self.get(key, 0) + inc

    def append(self, key, value):
        """Append a new value to a list statistic. Create if non existing."""
        item = self.get(key, [])
        item.append(value)
        self[key] = item

    def add_to_bin(self, key, value):
        """Add a value to statistic binned by time."""
        hour = (self._env.now % WEEK(1)) // HOUR(1)
        self.setdefault(key, {}).setdefault(hour, []).append(value)

    def dump_histogram_to_file(self, key, filename):
        """Dumps a histogram viriable to a file."""
        # pylint: disable=invalid-name
        with open(filename, 'w') as f:
            f.write('Day;Hour;Interval length;Frequency\n')
            for timestamp, data in self[key].items():
                f.write('{}\n'.format(';'.join(str(x) for x in (
                    INV_DAYS[timestamp // 24],
                    int(timestamp % 24),
                    ';'.join(repr(i) for i in data)))))

    def __getitem__(self, key):
        try:
            return super(Stats, self).__getitem__(key)
        except KeyError:
            return 0
