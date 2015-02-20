"""Request object. Mainly, it stores statistics."""

import logging
from base import Base
from stats import Stats

logger = logging.getLogger(__name__)


class Request(Base):
    """A request from the user.

    Asks for a server by waiting in the queue and then places the request.
    """

    def __init__(self, config, env, server):
        logger.debug('New Request')
        super(Request, self).__init__(config)
        self._env = env
        self._server = server
        self._stats = Stats(config, env)
        self._stats.increment('REQUESTS')

    def run(self):
        """Waits for a place in the queue and makes the request."""
        arrival_time = self._env.now
        self._stats.increment('WAITING_TIME', self._env.now - arrival_time)
        yield self._env.process(self._server.serve())
