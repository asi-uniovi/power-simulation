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

    def __init__(self, data: numpy.ndarray):
        self.__data = data
        self.__spline = None
        self.__mean = None
        self.__median = None

    @property
    def data(self) -> numpy.ndarray:
        """Returns the sample data used for the fitting."""
        return self.__data

    @property
    def mean(self) -> float:
        """Expected value of the distribution."""
        if self.__mean is None:
            self.__mean = numpy.mean(self.__data)
        return self.__mean

    @property
    def median(self) -> float:
        """Median of the distribution."""
        if self.__median is None:
            self.__median = numpy.median(self.__data)
        return self.__median

    def rvs(self, size: int = None) -> float:
        """Sample the spline that has the inverse CDF."""
        if self.__data.size < 2:
            return numpy.random.choice(self.__data, size=size)
        if self.__spline is None:
            self.__fit_spline()
        return self.__spline(numpy.random.random(size=size), nu=0)

    def extend(self, other: 'EmpiricalDistribution') -> None:
        """This extends this distribution with data from another."""
        self.__data = numpy.concatenate((self.__data, other.data))
        self.__spline = None
        self.__mean = None
        self.__median = None

    def multi_extend(
            self, others: typing.Iterable['EmpiricalDistribution']) -> None:
        """This extends this distribution with data from many others."""
        self.__data = numpy.concatenate(
            [self.__data] + [i.data for i in others])
        self.__spline = None
        self.__mean = None
        self.__median = None

    def __fit_spline(self) -> None:
        """Fits the distribution for generating random values."""
        self.__data.sort()
        t, c, k = scipy.interpolate.splrep(
            numpy.linspace(0, 1, self.__data.size), self.__data, k=1)
        self.__spline = scipy.interpolate.BSpline(t, c, k, extrapolate=False)

    def __len__(self) -> int:
        return self.__data.size

    def __iter__(self) -> float:
        yield from self.__data
