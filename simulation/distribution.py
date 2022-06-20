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

import logging
import numpy
import scipy.interpolate

logger = logging.getLogger(__name__)


class EmpiricalDistribution(object):
    """Empirical distribution according to the data provided.

    This is implemented with a cubic spline, which is faster than Law's ranking
    based method. More info:
    http://www.astroml.org/book_figures/chapter3/fig_clone_distribution.html
    """

    def __init__(self, data=None):
        self.__data = numpy.asanyarray([] if data is None else data)
        self.__spline = None

    @property
    def data(self):
        """Returns the sample data used for the fitting."""
        return self.__data

    @property
    def is_complete(self):
        """Indicate if the distribution has data."""
        return self.data.size > 0

    def rvs(self, size=1):
        """Sample the spline that has the inverse CDF."""
        if self.__data.size == 0:
            return None
        if self.__data.size == 1:
            return numpy.repeat(self.__data, repeats=size)
        if self.__spline is None:
            self.__fit_spline()
        return self.__spline(numpy.random.random(size=size), nu=0)

    def extend(self, others):
        """This extends this distribution with data from many others."""
        self.__spline = None
        self.__data = numpy.concatenate(
            [self.__data] + [i.data for i in others])

    def __fit_spline(self):
        """Fits the distribution for generating random values."""
        logger.debug('Fitting a spline with %d elements', len(self))
        self.__data.sort()
        t, c, k = scipy.interpolate.splrep(
            numpy.linspace(0, 1, self.__data.size), self.__data, k=1)
        self.__spline = scipy.interpolate.BSpline(t, c, k, extrapolate=False)

    def __len__(self):
        return self.__data.size

    def __iter__(self):
        yield from self.__data
