"""Small benchmark of the arrays and distributions."""

import gc
import sys
import timeit

import memory_profiler
import scipy.stats

# pylint: disable=unused-import
from distribution import EmpiricalDistribution


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
