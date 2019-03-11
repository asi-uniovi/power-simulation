#!/usr/bin/env python3
#
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

"""Small benchmark of the arrays and distributions."""

import gc
import sys
import timeit
import memory_profiler
import scipy.stats
from simulation.distribution import EmpiricalDistribution


@memory_profiler.profile
def main():
    """Repeat some fitting and print timings."""

    def gen_dataset(size):
        """Generates a random dataset from a normal distribution."""
        return scipy.stats.norm.rvs(size=size)

    def fit_dataset(dataset):
        """Fits the dataset for sampling."""
        return EmpiricalDistribution(dataset)

    for size in (1000, 10000, 100000, 1000000, 10000000):
        dataset = gen_dataset(size)

        gc.collect()
        fit_time = timeit.timeit(
            stmt='fit_dataset(dataset).rvs()',
            number=1000, globals=locals())

        gc.collect()
        rvs_time = timeit.timeit(
            stmt='fitted.rvs()',
            setup='fitted = fit_dataset(dataset) ; fitted.rvs()',
            number=1000, globals=locals())

        print('size = %d, fit_time = %.3f ms, rvs_time = %.3f ms' % (
            size, fit_time, rvs_time))


if __name__ == '__main__':
    sys.exit(main())
