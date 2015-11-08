"""Request object. Mainly, it stores statistics."""

import injector

from base import Base
from stats import Stats


@injector.inject(_stats=Stats)
class Request(Base):
    """A request from the user.

    Asks for a server by waiting in the queue and then places the request.
    """

    def run(self, computer):
        """Waits for a place in the queue and makes the request."""
        yield self._env.process(computer.serve())
