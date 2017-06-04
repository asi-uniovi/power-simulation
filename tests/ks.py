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
