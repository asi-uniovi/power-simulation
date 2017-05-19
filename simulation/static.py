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
import typing
import injector
import numpy
from simulation.configuration import Configuration

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
        format='%(asctime)s %(levelname)s(%(name)s): %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S',
        level=logging.DEBUG if config.get_arg('debug') else logging.INFO)
    logging.captureWarnings(True)


# pylint: disable=invalid-name,too-few-public-methods
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


def timestamp_to_day(timestamp: int) -> typing.Tuple[int, int]:
    """Converts from a simulation timestamp to the pair (day, hour)."""
    day = int((timestamp % WEEK(1)) // DAY(1))
    hour = int((timestamp % DAY(1)) // HOUR(1))
    return day, hour


# pylint: disable=invalid-name,no-member
def weight(x: float, ip: float, fp: float) -> float:
    """Linear increment between ip and fp function."""
    return numpy.maximum(0.0, numpy.minimum(1.0, (ip - x) / (ip - fp)))


# pylint: disable=invalid-name
def weighted_user_satisfaction(
        t: float, timeout: float, threshold: float) -> float:
    """Calculates the weighted satisfaction with a sigmoid."""
    return numpy.where(t < timeout, 1.0, weight(t - timeout, 60, threshold))


def user_satisfaction(t: float, timeout: float) -> float:
    """Calculates plain old user satisfaction."""
    return numpy.where(t < timeout, 1.0, 0.0)
