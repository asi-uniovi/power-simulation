"""Agent turning up and down the computers."""

import injector

from activity_distribution import ActivityDistribution
from base import Base


@injector.singleton
class Agent(Base):
    """Agent to manage compter status.

    This class controls the computer status and indicates when it should turn on
    or off, depending on the control policy installed.
    """

    @injector.inject(activity_distribution=ActivityDistribution)
    def __init__(self, activity_distribution):
        super(Agent, self).__init__()
        self._activity_distribution = activity_distribution

    def indicate_shutdown(self):
        """Indicates whether a computer should turndown."""
        return self._activity_distribution.shutdown_for_timestamp(
            self._env.now)

    def shutdown_interval(self):
        """Generates shutdown interval lengths."""
        return self._activity_distribution.off_interval_for_timestamp(
            self._env.now)
