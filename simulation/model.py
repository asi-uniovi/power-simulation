"""Representation of a model for a computer/user."""

import typing
import numpy
import scipy.optimize
from simulation.base import Base
from simulation.distribution import EmpiricalDistribution
from simulation.static import weighted_user_satisfaction


# pylint: disable=too-many-instance-attributes
class Model(Base):
    """Represents the model for a given hour.

    A model will store all the needed distributions and will offer basic
    functionality like timeout threshold calculation.
    """

    def __init__(self, inactivity: typing.List=None, activity: typing.List=None,
                 off_duration: typing.List=None,
                 off_fraction: typing.List=None):
        super(Model, self).__init__()
        self.__inactivity = EmpiricalDistribution(inactivity or [])
        self.__activity = EmpiricalDistribution(activity or [])
        self.__off_duration = EmpiricalDistribution(off_duration or [])
        self.__off_fraction = off_fraction or []
        self.__optimal_timeout = None
        self.__satisfaction_threshold = self.get_config_int(
            'satisfaction_threshold', section='stats')
        self.__target_satisfaction = self.get_config_int('target_satisfaction')
        self.__xmax = self.get_config_float('xmax', section='trace')
        self.__xmin = self.get_config_float('xmin', section='trace')

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

    @property
    def is_complete(self) -> bool:
        """Indicates if the model has all distributions."""
        return (self.inactivity and self.activity and self.off_duration
                and self.off_fraction)

    def resolve_key(self, key: str) -> EmpiricalDistribution:
        """Matches histograms and keys."""
        if key == 'ACTIVITY_TIME':
            return self.activity
        elif key == 'INACTIVITY_TIME':
            return self.inactivity
        elif key == 'USER_SHUTDOWN_TIME':
            return self.off_duration
        elif key == 'AUTO_SHUTDOWN_TIME':
            return EmpiricalDistribution([])
        elif key == 'IDLE_TIME':
            return EmpiricalDistribution([])
        raise KeyError('Invalid key for histogram.')

    def extend(self, other: 'Model') -> None:
        """Appends the data from another model to this one."""
        # pylint: disable=no-member
        self.__inactivity.extend(other.inactivity)
        self.__activity.extend(other.activity)
        self.__off_duration.extend(other.off_duration)
        self.__off_fraction += other.off_fraction

    def optimal_idle_timeout(self) -> float:
        """Does the search for the optimal timeout for this model."""
        if self.__optimal_timeout is None:
            self.__optimal_timeout = self.__optimal_timeout_search()
        return self.__optimal_timeout

    def __optimal_timeout_search(self) -> float:
        """Uses the bisection method to find the timeout for the target."""

        def f(x):  # pylint: disable=invalid-name
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
                return self.__xmax
            return self.__xmin
