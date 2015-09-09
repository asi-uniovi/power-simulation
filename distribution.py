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
        return [self.rvs() for _ in range(n)]


class EmpiricalDistribution(Distribution):
    """Empirical distribution according to the data provided."""

    def __init__(self, data):
        ecdf = sm.distributions.ECDF(numpy.array(data, copy=True))
        self._inverse = sm.distributions.monotone_fn_inverter(ecdf, ecdf.x)

    def rvs(self):
        return float(self._inverse(numpy.random.random()))


class SimpleRateDistribution(Distribution):
    """This distribution returns 1 with a probability of rate."""

    def __init__(self, rate):
        self._rate = rate

    def rvs(self):
        return self._rate
