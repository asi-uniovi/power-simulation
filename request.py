"""Request object. Mainly, it stores statistics."""

import injector
import logging

from base import Base
from stats import Stats

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Request(Base):
    """A request from the user.

    Asks for a server by waiting in the queue and then places the request.
    """

    @injector.inject(stats=Stats)
    def __init__(self, stats):
        super(Request, self).__init__()
        self._stats = stats
        self._stats.append('REQUEST_COUNT', 1)

    def run(self, computer):
        """Waits for a place in the queue and makes the request."""
        arrival_time = self._env.now
        self._stats.append('WAITING_TIME', self._env.now - arrival_time)
        yield self._env.process(computer.serve())
