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

import scipy.stats

from simulation.distribution import EmpiricalDistribution

ALPHA = 0.05
SIZE = 10000


def ks_2samp(original_data):
    """Test the fitness of the empirical distribution to a dataset."""
    fitted_data = EmpiricalDistribution(data=original_data).rvs(size=SIZE)
    _, pvalue = scipy.stats.ks_2samp(original_data, fitted_data)
    return pvalue > ALPHA


def test_norm():
    """Test fitness with the normal distribution"""
    assert ks_2samp(scipy.stats.norm().rvs(size=SIZE))
    assert ks_2samp(scipy.stats.norm(loc=7, scale=21).rvs(size=SIZE))


def test_exp():
    """Test fitness with the exponential distribution"""
    assert ks_2samp(scipy.stats.expon().rvs(size=SIZE))


def test_pareto():
    """Test fitness with the pareto distribution"""
    assert ks_2samp(scipy.stats.pareto(b=1).rvs(size=SIZE))
