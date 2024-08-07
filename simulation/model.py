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

"""Representation of a model for a computer/user."""

import injector
import typing
import numpy
import scipy.optimize
from simulation.configuration import Configuration
from simulation.distribution import EmpiricalDistribution
from simulation.static import user_satisfaction
from simulation.static import weighted_user_satisfaction


class Model(object):
    """Represents the model for a given hour.

    A model will store all the needed distributions and will offer basic
    functionality like timeout threshold calculation.
    """

    @injector.inject
    @injector.noninjectable('xmax', 'xmin', 'inactivity', 'activity',
                            'off_duration', 'off_fraction')
    def __init__(self, config: Configuration, xmax: float,
                 xmin: float, inactivity: typing.List = None,
                 activity: typing.List = None,
                 off_duration: typing.List = None,
                 off_fraction: typing.List = None):
        super(Model, self).__init__()
        self.__inactivity = EmpiricalDistribution(inactivity)
        self.__activity = EmpiricalDistribution(activity)
        self.__off_duration = EmpiricalDistribution(off_duration)
        self.__off_fraction = off_fraction or [0.0]
        self.__optimal_timeout = None
        self.__satisfaction_threshold = config.get_config_int(
            'satisfaction_threshold')
        self.__target_satisfaction = config.get_config_int(
            'target_satisfaction')
        self.__xmax = xmax
        self.__xmin = xmin
        self.__tested = None

    @property
    def is_complete(self) -> bool:
        """Indicates if the model has all the minimum distributions."""
        return self.inactivity.is_complete

    @property
    def inactivity(self) -> EmpiricalDistribution:
        """Inactivity distribution."""
        return self.__inactivity

    @property
    def activity(self) -> EmpiricalDistribution:
        """Activity distribution."""
        return self.__activity

    @property
    def off_duration(self) -> EmpiricalDistribution:
        """Off intervals distribution."""
        return self.__off_duration

    @property
    def off_fraction(self) -> typing.List:
        """Off proportions."""
        return self.__off_fraction

    def test_timeout(
            self, timeout: float,
            retest: bool = False) -> typing.Tuple[float, float, float, float]:
        """Calculate analytically the US and RI for a given timeout."""
        if self.__tested is None or retest:
            wus = (numpy.sum(weighted_user_satisfaction(
                self.inactivity.data, timeout, self.__satisfaction_threshold))
                   / len(self.inactivity.data)) * 100
            us = (numpy.sum(user_satisfaction(self.inactivity.data, timeout))
                  / len(self.inactivity.data)) * 100
            ri = numpy.sum(numpy.where(self.inactivity.data > timeout,
                                       self.inactivity.data - timeout, 0.0))
            ti = numpy.sum(self.inactivity.data)
            self.__tested = (wus, us, ri, ti)
        return self.__tested

    def resolve_key(self, key: str) -> EmpiricalDistribution:
        """Matches histograms and keys."""
        if key == 'ACTIVITY_TIME':
            return self.activity
        elif key == 'INACTIVITY_TIME':
            return self.inactivity
        elif key == 'USER_SHUTDOWN_TIME':
            return self.off_duration
        elif key == 'AUTO_SHUTDOWN_TIME':
            return EmpiricalDistribution()
        raise KeyError('Invalid key for histogram.')

    def extend(self, others: typing.List['Model']) -> None:
        """Appends the data from another model to this one."""
        self.__inactivity.extend([i.inactivity for i in others])
        self.__activity.extend([i.activity for i in others])
        self.__off_duration.extend([i.off_duration for i in others])
        self.__off_fraction.extend(i.off_fraction for i in others)
        self.__optimal_timeout = None
        self.__tested = None

    def optimal_idle_timeout(self) -> float:
        """Does the search for the optimal timeout for this model."""
        if self.__optimal_timeout is None:
            self.__optimal_timeout = min(self.__optimal_timeout_search(),
                                         self.__satisfaction_threshold)
        return self.__optimal_timeout

    def __optimal_timeout_search(self) -> float:
        """Uses the bisection method to find the timeout for the target."""

        def f(x):
            """Trasposed function to optimize via root finding."""
            return (numpy.mean(weighted_user_satisfaction(
                self.inactivity.data, x, self.__satisfaction_threshold))
                    * 100 - self.__target_satisfaction)

        try:
            return scipy.optimize.brentq(f, self.__xmin, self.__xmax, xtol=1)
        except ValueError:
            # If the function has no root, means that we cannot achieve the
            # satisfaction target, therefore, if we provide the max value, we
            # ensure to, at least, be as close as possible.
            if f(self.__xmax) > f(self.__xmin):
                return self.__satisfaction_threshold
            return self.__xmin
