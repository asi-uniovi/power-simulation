"""Some useful statistical distributions."""

import abc
import math
import random
import statistics


class Distribution(object, metaclass=abc.ABCMeta):
    """Base distribution class."""

    def __init__(self, data):
        self.__data = sorted(data)
        self.__mean = statistics.mean(self.data)
        self.__median = statistics.median(self.data)

    @property
    def data(self):
        """Returns the sample data used for the fitting."""
        return self.__data

    @property
    def mean(self):
        """Expected value of the distribution."""
        return self.__mean

    @property
    def median(self):
        """Median of the distribution."""
        return self.__median

    @property
    def sample_size(self):
        """How much data we got for this distribution."""
        return len(self.data)

    def rvs(self):
        """This samples the distribution for one value."""
        raise NotImplementedError


class DiscreteUniformDistribution(Distribution):
    """Uniform distribution over a set of values."""

    def rvs(self):
        """One item from the sample."""
        return random.choice(self.data)


class EmpiricalDistribution(Distribution):
    """Empirical distribution according to the data provided."""

    def __init__(self, data):
        super(EmpiricalDistribution, self).__init__(data)
        self.__diffs = [data[i + 1] - data[i] for i in range(len(data) - 1)]
        self.__diffs.append(0)

    def rvs(self):
        """Implementation from "Simulation Modeling and Analysis, 5e"."""
        # pylint: disable=invalid-name
        p = (self.sample_size - 1) * random.random()
        i = int(math.floor(p) + 1)
        return self.data[i] + (p - i + 1) * self.__diffs[i]
