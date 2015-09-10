"""Some useful statistical distributions."""

import abc
import logging
import numpy
import six
import statsmodels.api as sm

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Distribution(six.with_metaclass(abc.ABCMeta)):

    def rvs(self):
        """This samples the distribution for one value."""
        raise NotImplementedError

    def xrvs(self, n):
        """Sample the distribution several times."""
        return numpy.asarray([self.rvs() for _ in range(n)])


class EmpiricalDistribution(Distribution):
    """Empirical distribution according to the data provided."""

    def __init__(self, data):
        ecdf = sm.distributions.ECDF(numpy.array(data, copy=True))
        self._inverse = sm.distributions.monotone_fn_inverter(ecdf, ecdf.x)

    def rvs(self):
        return float(self._inverse(numpy.random.random()))


class BinomialDistribution(Distribution):
    """The binomial distribution."""

    def __init__(self, n, p):
        self._n = n
        self._p = p

    def rvs(self):
        return numpy.random.binomial(self._n, self._p)

    def xrvs(self, n):
        return numpy.random.binomial(self._n, self._p, n)


class BernoulliDistribution(BinomialDistribution):
    """This distribution returns 1 with a probability of p."""

    def __init__(self, p):
        super(BernoulliDistribution, self).__init__(1, p)
