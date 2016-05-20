"""Some useful statistical distributions."""

import abc
import functools

import numpy


class Distribution(object, metaclass=abc.ABCMeta):
    """Base distribution class."""

    def __init__(self, data):
        self.__data = numpy.sort(data)

    @property
    def data(self):
        """Returns the sample data used for the fitting."""
        return self.__data

    @property
    @functools.lru_cache()
    def mean(self):
        """Expected value of the distribution."""
        return numpy.mean(self.data)

    @property
    @functools.lru_cache()
    def median(self):
        """Median of the distribution."""
        return numpy.median(self.data)  # pylint: disable=no-member

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
        return numpy.random.choice(self.data)  # pylint: disable=no-member


class EmpiricalDistribution(Distribution):
    """Empirical distribution according to the data provided."""

    def __init__(self, data):
        super(EmpiricalDistribution, self).__init__(data + [max(data)])

    @property
    def sample_size(self):
        """How much data we got for this distribution."""
        return len(self.data) - 1

    def rvs(self):
        """Sample the inverse and try again in nan."""
        p = (self.sample_size - 2) * numpy.random.random()
        i = int(numpy.floor(p) + 1)
        return self.data[i] + (p - i + 1) * (self.data[i + 1] - self.data[i])
