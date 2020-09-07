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

import numpy
import pytest
import scipy.stats

from simulation.distribution import EmpiricalDistribution

ALPHA = 0.01
SIZE = 50000


@pytest.fixture(scope='session', autouse=True)
def setup_numpy():
    """Set the random seed to the same value."""
    numpy.random.seed(13)


@pytest.mark.parametrize('original_dist', [
    scipy.stats.norm(),
    scipy.stats.norm(loc=7, scale=21),
    scipy.stats.expon(),
    scipy.stats.pareto(b=1)])
def test_ks_2samp(original_dist):
    """Test the fitness of the empirical distribution to a dataset."""
    original_data = original_dist.rvs(size=SIZE)
    fitted_data = EmpiricalDistribution(data=original_data).rvs(size=SIZE)
    # H0 is samples are from the same distribution.
    _, pvalue = scipy.stats.ks_2samp(original_data, fitted_data)
    # Assert we can't reject the H0.
    assert pvalue >= ALPHA


def test_merge():
    """Test the merging of distributions."""
    merged = EmpiricalDistribution(
        data=scipy.stats.norm(loc=10, scale=4).rvs(size=SIZE))
    merged.extend([EmpiricalDistribution(
        data=scipy.stats.norm(loc=20, scale=7).rvs(size=SIZE))])
    one = EmpiricalDistribution(data=numpy.concatenate((
        scipy.stats.norm(loc=10, scale=4).rvs(size=SIZE),
        scipy.stats.norm(loc=20, scale=7).rvs(size=SIZE))))
    # H0 is samples are from the same distribution.
    _, pvalue = scipy.stats.ks_2samp(one.rvs(size=SIZE), merged.rvs(size=SIZE))
    # Assert we can't reject the H0.
    assert pvalue >= ALPHA
