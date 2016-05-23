"""Some useful statistical distributions."""

import abc

import numpy


class Distribution(object, metaclass=abc.ABCMeta):
    """Base distribution class."""

    def __init__(self, data):
        self.__data = numpy.ascontiguousarray(data)
        self.__mean = numpy.mean(self.__data)
        self.__median = numpy.median(self.__data)
        self.__sample_size = numpy.size(self.__data)

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
        return self.__sample_size

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
        super(EmpiricalDistribution, self).__init__(numpy.sort(data))
        self.__diffs = numpy.ascontiguousarray(
            [self.data[i + 1] - self.data[i]
             for i in range(self.sample_size - 1)] + [0.0])

    def rvs(self):
        """Implementation from "Simulation Modeling and Analysis, 5e"."""
        # pylint: disable=invalid-name
        p = (self.sample_size - 1) * numpy.random.random()
        i = int(numpy.floor(p) + 1)
        return self.data[i] + (p - i + 1) * self.__diffs[i]
