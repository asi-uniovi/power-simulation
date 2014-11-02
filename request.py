"""Request object. Mainly, it stores statistics."""

import logging
from base import Base
from server import Server
from stats import Stats

logger = logging.getLogger(__name__)


class Request(Base):
    """A request from the user.

    Asks for a server by waiting in the queue and then places the request.
    """

    def __init__(self, config, env, queue):
        super(Request, self).__init__(config)
        self._env = env
        self._queue = queue
        self._stats = Stats()
        self._stats.increment('REQUESTS')
        logger.debug('A new request is created')

    def run(self):
        """Waits for a place in the queue and makes the request."""
        with self._queue.request() as req:
            arrival_time = self._env.now
            yield req
            self._stats.increment('WAITING_TIME', self._env.now - arrival_time)
            yield self._env.process(Server(self._config, self._env).serve())
