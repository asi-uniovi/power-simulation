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

    def __init__(self, data: typing.Any):
        self.__data = numpy.asarray(data)
        self.__tck = None
        self.__cdf = None

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

    def rvs(self, size: int = None) -> float:
        """Sample the spline that has the inverse CDF."""
        if self.__data.size < 2:
            return numpy.random.choice(self.__data, size=size)
        if self.__tck is None:
            self.__fit_tck()
        return scipy.interpolate.splev(
            numpy.random.random(size=size), self.__tck, der=0)

    def cdf(self, vals: numpy.ndarray) -> numpy.ndarray:
        """Cumulative distribution function."""
        if self.__data.size < 2:
            return numpy.zeros(len(vals))
        if self.__cdf is None:
            self.__fit_cdf()
        return numpy.maximum(0, numpy.minimum(
            1, scipy.interpolate.splev(vals, self.__cdf, der=0)))

    def extend(self, other: 'EmpiricalDistribution') -> None:
        """This extends this distribution with data from another."""
        self.__data = numpy.append(self.__data, other.data)
        self.__tck = None
        self.__cdf = None

    def __fit_tck(self) -> None:
        """Fits the distribution for generating random values."""
        self.__data.sort()
        self.__tck = scipy.interpolate.splrep(
            numpy.linspace(0, 1, self.__data.size), self.__data, k=1)

    def __fit_cdf(self) -> None:
        """Fits the distribution for generating CDF."""
        self.__data.sort()
        self.__cdf = scipy.interpolate.splrep(
            self.__data, numpy.linspace(0, 1, self.__data.size), k=1)

    def __len__(self) -> int:
        return len(self.__data)

    def __iter__(self) -> float:
        yield from self.__data
