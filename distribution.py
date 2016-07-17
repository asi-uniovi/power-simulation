"""Some useful statistical distributions."""

import abc

import numpy


class Distribution(object, metaclass=abc.ABCMeta):
    """Base distribution class."""

    def __init__(self, data):
        self.__data = numpy.sort(data)
        self.__data.setflags(write=False)

    @property
    def data(self):
        """Returns the sample data used for the fitting."""
        return self.__data

    @property
    def mean(self):
        """Expected value of the distribution."""
        return numpy.mean(self.__data)

    @property
    def median(self):
        """Median of the distribution."""
        return numpy.median(self.__data)

    @property
    def sample_size(self):
        """How much data we got for this distribution."""
        return len(self.__data)

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
        super(EmpiricalDistribution, self).__init__(sorted(data))
        self.__diffs = numpy.asarray([self.data[i + 1] - self.data[i]
            for i in range(self.sample_size - 1)] + [0.0])
        self.__diffs.setflags(write=False)

    def rvs(self):
        """Implementation from "Simulation Modeling and Analysis, 5e"."""
        # pylint: disable=invalid-name
        p = (self.sample_size - 1) * numpy.random.random()
        i = int(numpy.floor(p) + 1)
        return self.data[i] + (p - i + 1) * self.__diffs[i]
