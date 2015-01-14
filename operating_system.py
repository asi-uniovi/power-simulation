"""A simulation object for the OS of the server."""

import logging
from base import Base
from policy import TimeoutPolicy
from stats import Stats

logger = logging.getLogger(__name__)


class SimpleTimeoutOS(Base):
    """A simple simulation object that mimicks an OS.

    Controls the timeout of devices and makes the computer sleep.
    """

    def __init__(self, config, env, server):
        super(SimpleTimeoutOS, self).__init__(config)
        self._env = env
        self._server = server
        # Simple default policy.
        self._policies = {'equilibrada': TimeoutPolicy(config, env, server, 30)}
        self._active_policy = self._policies['equilibrada']
        # Start the policy loop to control the server.
        self._env.process(self.__power_manager_loop())

    @property
    def policies(self):
        return self._policies.values()

    def change_policy(self, policy):
        """Alters the current setup policy."""
        assert policy in self._policies.values()
        self._active_policy = policy

    def __power_manager_loop(self):
        """Runs the power manager of the OS to control the server."""
        while True:
            self._active_policy.policy_eval()
            yield self._env.timeout(self._active_policy._threshold)
