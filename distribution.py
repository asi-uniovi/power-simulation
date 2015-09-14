"""Some useful statistical distributions."""

import abc
import logging
import numpy
import random
import six
import statsmodels.api as sm

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Distribution(six.with_metaclass(abc.ABCMeta)):
    """Base distribution class."""

    def rvs(self):
        """This samples the distribution for one value."""
        raise NotImplementedError

    # pylint: disable=invalid-name
    def xrvs(self, n):
        """Sample the distribution several times."""
        # pylint: disable=no-member
        return numpy.asarray([self.rvs() for _ in range(n)])


class DiscreteUniformDistribution(Distribution):
    """Uniform distribution over a set of values."""

    def __init__(self, *data):
        self._data = data

    def rvs(self):
        return self.xrvs(1)

    def xrvs(self, n):
        return random.sample(self._data, n)


class EmpiricalDistribution(Distribution):
    """Empirical distribution according to the data provided."""

    def __init__(self, *data):
        # pylint: disable=no-member
        ecdf = sm.distributions.ECDF(numpy.array(data, copy=True))
        self._inverse = sm.distributions.monotone_fn_inverter(ecdf, ecdf.x)

    def rvs(self):
        return float(self._inverse(numpy.random.random()))


class BinomialDistribution(Distribution):
    """The binomial distribution."""

    def __init__(self, N, p):
        # pylint: disable=invalid-name
        self._N = N
        self._p = p

    def rvs(self):
        return self.xrvs(1)

    def xrvs(self, n):
        # pylint: disable=no-member
        return numpy.random.binomial(self._N, self._p, n)


class BernoulliDistribution(BinomialDistribution):
    """This distribution returns 1 with a probability of p."""

    def __init__(self, p):
        super(BernoulliDistribution, self).__init__(1, p)
