"""Some useful statistical distributions."""

import abc
import random

import numpy
import statsmodels.api as sm


class Distribution(object, metaclass=abc.ABCMeta):
    """Base distribution class."""

    def __init__(self, sample_size, data):
        self.__data = data
        self.__sample_size = sample_size

    @property
    def mean(self):
        """Expected value of the distribution."""
        return numpy.mean(self.data)

    @property
    def median(self):
        """Median of the distribution."""
        return numpy.median(self.data)  # pylint: disable=no-member

    @property
    def sample_size(self):
        """How much data we got for this distribution."""
        return self.__sample_size

    def rvs(self):
        """This samples the distribution for one value."""
        raise NotImplementedError

    def xrvs(self, n):  # pylint: disable=invalid-name
        """Sample the distribution several times."""
        return numpy.asarray([self.rvs() for _ in range(n)])

    @property
    def data(self):
        """Returns the sample data used for the fitting."""
        return self.__data


class DiscreteUniformDistribution(Distribution):
    """Uniform distribution over a set of values."""

    def __init__(self, sample_size, *data):
        super(DiscreteUniformDistribution, self).__init__(sample_size, data)

    def rvs(self):
        """One item from the sample."""
        return self.xrvs(1)[0]

    def xrvs(self, n):
        """Just get a sample with the repetition from the data."""
        return random.sample(self.data, n)


class EmpiricalDistribution(Distribution):
    """Empirical distribution according to the data provided."""

    def __init__(self, sample_size, *data):
        super(EmpiricalDistribution, self).__init__(sample_size, data)
        ecdf = sm.distributions.ECDF(numpy.array(data, copy=True))
        self.__inverse = sm.distributions.monotone_fn_inverter(ecdf, ecdf.x)

    def rvs(self):
        """Sample the inverse and try again in nan."""
        # TODO(m3drano): This might just block in a NaN if the distribution is
        # malformed, for instance when it has only one value.
        ret = float(self.__inverse(numpy.random.random()))
        while numpy.isnan(ret):  # pylint: disable=no-member
            ret = float(self.__inverse(numpy.random.random()))
        return ret


class BinomialDistribution(Distribution):
    """The binomial distribution."""

    def __init__(self, N, p):
        super(BinomialDistribution, self).__init__(0, [])
        self.__N = N  # pylint: disable=invalid-name
        self.__p = p

    @property
    def mean(self):
        return self.__N * self.__p

    @property
    def median(self):
        # https://dx.doi.org/10.1111%2Fj.1467-9574.1980.tb00681.x
        return round(self.__N * self.__p)

    def rvs(self):
        return self.xrvs(1)[0]

    def xrvs(self, n):
        # pylint: disable=no-member
        return numpy.random.binomial(self.__N, self.__p, n)


class BernoulliDistribution(BinomialDistribution):
    """This distribution returns 1 with a probability of p."""

    def __init__(self, p):
        super(BernoulliDistribution, self).__init__(1, p)
