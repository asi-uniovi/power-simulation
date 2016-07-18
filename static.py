"""Static definitions, such as constants."""

import cProfile
import functools
import logging

import injector
import numpy

from configuration import Configuration


DAYS = {
    'Sunday': 0,
    'Monday': 1,
    'Tuesday': 2,
    'Wednesday': 3,
    'Thursday': 4,
    'Friday': 5,
    'Saturday': 6,
}

# All this functions convert to seconds.
HOUR = lambda x: x * 3600.0
DAY = lambda x: x * HOUR(24)
WEEK = lambda x: x * DAY(7)

# And these to bytes.
KB = lambda x: x << 10
MB = lambda x: x << 20


# pylint: disable=too-few-public-methods
class HashableArray(object):
    """This is just contains the NumPy array and the hash."""

    def __init__(self, data, sort=False):
        super(HashableArray, self).__init__()
        try:
            self.__hash = hash(data)
        except TypeError:
            self.__hash = hash(tuple(data))
        if sort:
            self.__array = numpy.sort(data)
        else:
            self.__array = numpy.asarray(data)
        self.__array.setflags(write=False)

    @property
    def array(self):
        """Returns the enclosed array."""
        return self.__array

    def __getitem__(self, index):
        """Make this object subscriptable."""
        return self.__array[index]

    def __len__(self):
        """The len is always the len of the enclosed."""
        return len(self.__array)

    def __hash__(self):
        """Returns the hash of the enclosing."""
        return self.__hash


@injector.inject(config=Configuration)
def config_logging(config):
    """Sets logging basic config"""
    logging.basicConfig(
        format='%(asctime)s %(levelname)s(%(name)s): %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S',
        level=logging.DEBUG if config.get_arg('debug') else logging.INFO)
    logging.captureWarnings(True)


@injector.inject(_config=Configuration)
# pylint: disable=invalid-name,too-few-public-methods
class profile(object):
    """Decorator to run a function and generate a trace."""

    def __call__(self, func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wraps the function generating a trace."""
            if self._config.get_arg('trace'):  # pylint: disable=no-member
                profiler = cProfile.Profile()
                profiler.enable()

            ret = func(*args, **kwargs)

            if self._config.get_arg('trace'):  # pylint: disable=no-member
                profiler.create_stats()
                profiler.dump_stats('trace')

            return ret

        return wrapper


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


# pylint: disable=invalid-name
def weight(x, ip, fp):
    """Linear increment between ip and fp function."""
    return max(0.0, min(1.0, (ip - x) / (ip - fp)))


# pylint: disable=invalid-name
def weighted_user_satisfaction(t, timeout, threshold):
    """Calculates the weighted satisfaction with a sigmoid."""
    if t < timeout:
        return 1.0
    else:
        return weight(t - timeout, 60, threshold)
