"""Small Kolmogorov-Smirnov test for fitting validity."""

import sys
import scipy.stats
# pylint: disable=import-error
from simulation.distribution import EmpiricalDistribution

ALPHA = 0.05
SIZE = 10000


# pylint: disable=invalid-name
def main():
    """Repeat some fitting and print timings."""
    dataset = EmpiricalDistribution(scipy.stats.norm.rvs(size=SIZE))

    D, pvalue = scipy.stats.kstest(dataset.rvs, 'norm', N=SIZE)
    print('D = %.4f, p-value = %.4f' % (D, pvalue))
    if pvalue < ALPHA:
        print('Reject H₀ at α = %.2f: Distributions are different!' % ALPHA)

    D, pvalue = scipy.stats.ks_2samp(
        dataset.rvs(size=SIZE), scipy.stats.norm.rvs(size=SIZE))
    print('D = %.4f, p-value = %.4f' % (D, pvalue))
    if pvalue < ALPHA:
        print('Reject H₀ at α = %.2f: Distributions are different!' % ALPHA)


if __name__ == '__main__':
    sys.exit(main())
