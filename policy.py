"""Basic power management policies for the computer."""

import logging
from base import Base
from stats import Stats

logger = logging.getLogger(__name__)


class TimeoutPolicy(Base):
    """A simple shutdown policy based on timeout.

    Shutdowns the computer when a time threshold of inactivity is surpassed.
    """

    def __init__(self, config, env, server, threshold):
        super(TimeoutPolicy, self).__init__(config)
        self._stats = Stats()
        self._env = env
        self._threshold = threshold
        self._server = server

    def policy_eval(self):
        """Runs the policy loop to control the power status of the server."""
        logger.debug('Policy control loop (%d)', self._env.now)
