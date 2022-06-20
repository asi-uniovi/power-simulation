# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Static definitions, such as constants."""

import cProfile
import functools
import logging
import math
import time
import typing
import injector
import numpy
import scipy.stats
from simulation.configuration import Configuration

HISTOGRAMS = sorted((
    'USER_SHUTDOWN_TIME',
    'AUTO_SHUTDOWN_TIME',
    'ACTIVITY_TIME',
    'INACTIVITY_TIME',
))

T = typing.TypeVar('T')

DAYS = {
    'Sunday': 0,
    'Monday': 1,
    'Tuesday': 2,
    'Wednesday': 3,
    'Thursday': 4,
    'Friday': 5,
    'Saturday': 6,
}

REVERSE_DAYS = {v: k for k, v in DAYS.items()}

# All this functions convert to seconds.
HOUR = lambda x: x * 3600.0
DAY = lambda x: x * HOUR(24)
WEEK = lambda x: x * DAY(7)

# And these to bytes.
KB = lambda x: x << 10
MB = lambda x: x << 20


def config_logging(config: Configuration) -> None:
    """Sets logging basic config"""
    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=logging.DEBUG if config.get_arg('debug') else logging.INFO)
    logging.captureWarnings(True)


class profile:
    """Decorator to run a function and generate a trace."""

    @injector.inject
    def __init__(self, config: Configuration):
        super(profile, self).__init__()
        self.__config = config

    def __call__(self, func: typing.Callable[..., T]) -> T:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wraps the function generating a trace."""
            if self.__config.get_arg('trace'):
                profiler = cProfile.Profile()
                profiler.enable()

            ret = func(*args, **kwargs)

            if self.__config.get_arg('trace'):
                profiler.create_stats()
                profiler.dump_stats('trace')

            return ret

        return wrapper


def timed(func):
    """Decorator to measure and print the time of this function."""
    logger = logging.getLogger(func.__module__)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Wraps the function to time."""
        t = time.process_time()
        result = func(*args, **kwargs)
        logger.debug('Execution time of %s.%s(): %.4f s',
                     func.__module__, func.__name__, time.process_time() - t)
        return result

    return wrapper


def timestamp_to_day(timestamp: int) -> typing.Tuple[int, int]:
    """Converts from a simulation timestamp to the pair (day, hour)."""
    day = int((timestamp % WEEK(1)) // DAY(1))
    hour = int((timestamp % DAY(1)) // HOUR(1))
    return day, hour


def timestamp_to_hour(timestamp: int) -> int:
    """Converts from a simulation timestamp to a simulation hour."""
    hour = int((timestamp % WEEK(1)) // HOUR(1))
    assert hour >= 0 and hour <= 167
    return hour


def hour_to_day(hour: int) -> typing.Tuple[int, int]:
    """Converts from a simulation hour to the pair (day, hour)."""
    day = int(hour // 24)
    hour = int(hour % 24)
    return day, hour


def previous_hour(day: int, hour: int) -> typing.Tuple[int, int]:
    """Gets the previous hour with wrap."""
    hour -= 1
    if hour < 0:
        hour = 23
        day -= 1
        if day < 0:
            day = 6
    return day, hour


def weight(x: float, ip: float, fp: float) -> float:
    """Linear increment between ip and fp function."""
    return numpy.maximum(0.0, numpy.minimum(1.0, (ip - x) / (ip - fp)))


def weighted_user_satisfaction(
        t: float, timeout: float, threshold: float) -> float:
    """Calculates the weighted satisfaction with a sigmoid."""
    return numpy.where(t < timeout, 1.0, weight(t - timeout, 60, threshold))


def user_satisfaction(t: float, timeout: float) -> float:
    """Calculates plain old user satisfaction."""
    return numpy.where(t < timeout, 1.0, 0.0)


def generate_servers(size: int) -> typing.List[str]:
    """Generates a list of servers randomly generated."""
    fill = math.ceil(math.log(size, 10))
    return ['workstation' + str(i).zfill(fill) for i in range(size)]


def draw_from_distribution(distribution: scipy.stats.rv_continuous,
                           min_value: float = 0.0,
                           max_value: float = float('inf')) -> float:
    """Gets a value from a distribution bounding the limit."""
    rnd = distribution.rvs()
    if not rnd:
        return min_value
    while rnd < min_value or rnd > max_value:
        rnd = distribution.rvs()
    return rnd
