"""Some useful statistical distributions."""

import typing
import numpy
import scipy.interpolate


class EmpiricalDistribution:
    """Empirical distribution according to the data provided.

    This is implemented with a cubic spline, which is faster than Law's ranking
    based method. More info:
    http://www.astroml.org/book_figures/chapter3/fig_clone_distribution.html
    """

    def __init__(self, data: typing.Any):
        self.__data = numpy.asarray(data)
        self.__tck = None

    @property
    def data(self) -> numpy.ndarray:
        """Returns the sample data used for the fitting."""
        return self.__data

    @property
    def mean(self) -> float:
        """Expected value of the distribution."""
        return numpy.mean(self.__data)

    @property
    def median(self) -> float:
        """Median of the distribution."""
        return numpy.median(self.__data)

    def rvs(self, size: int=None) -> float:
        """Sample the spline that has the inverse CDF."""
        if self.__data.size < 2:
            # pylint: disable=no-member
            return numpy.random.choice(self.__data, size=size)
        if self.__tck is None:
            self.__fit()
        return scipy.interpolate.splev(
            numpy.random.random(size=size), self.__tck, der=0)

    def extend(self, other: 'EmpiricalDistribution') -> None:
        """This extends this distribution with data from another."""
        self.__data = numpy.append(self.__data, other.data)
        self.__tck = None

    def __fit(self) -> None:
        """Fits the distribution for generating random values."""
        self.__data.sort()
        self.__tck = scipy.interpolate.splrep(
            numpy.linspace(0, 1, self.__data.size), self.__data, k=1)

    def __len__(self) -> int:
        return self.__data.size

    def __iter__(self) -> float:
        for i in self.__data:
            yield i