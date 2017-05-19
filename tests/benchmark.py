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
# pylint: disable=import-error,unused-import
from simulation.distribution import EmpiricalDistribution


def setup(size):
    """Generates a random dataset from a normal distribution."""
    gc.enable()
    return list(scipy.stats.norm.rvs(size=size)), []


@memory_profiler.profile
def main():
    """Repeat some fitting and print timings."""
    for size in (10, 100, 1000, 10000):
        print('size = %d, timeit = %.3f ms' % (size, min(timeit.repeat(
            stmt='res.append(EmpiricalDistribution(dataset))',
            setup='dataset, res = setup(%d)' % size,
            repeat=3, number=100, globals=globals())) * 10.0))


if __name__ == '__main__':
    sys.exit(main())
