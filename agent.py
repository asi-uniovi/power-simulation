"""Agent turning up and down the computers."""

import injector

from activity_distribution import ActivityDistribution
from base import Base


@injector.singleton
@injector.inject(_activity_distribution=ActivityDistribution)
class Agent(Base):
    """Agent to manage compter status.

    This class controls the computer status and indicates when it should turn on
    or off, depending on the control policy installed.
    """

    def __init__(self):
        super(Agent, self).__init__()
        self.__pcs_done = 0
        self.__pcs_to_do = self.__fraction_to_shutdown()
        self._env.process(self.__upgrade_loop())

    def indicate_shutdown(self):
        """Indicates whether a computer should turndown."""
        if self.__pcs_done < self.__pcs_to_do:
            self.__pcs_done += 1
            return True
        return False

    def shutdown_interval(self):
        """Generates shutdown interval lengths."""
        try:
            return round(self._activity_distribution.off_interval_for_timestamp(
                self._env.now))
        except ValueError:
            return 0

    def __fraction_to_shutdown(self):
        """Indicates how many PCs we should be turning down right now."""
        return round(self._activity_distribution.shutdown_for_timestamp(
            self._env.now) * self._activity_distribution.servers)

    def __upgrade_loop(self):
        """Upgrades the configuration for the target turndown for this hour."""
        while True:
            yield self._env.timeout(3600)
            self.__pcs_done = 0
            self.__pcs_to_do = self.__fraction_to_shutdown()
