import numpy

SERVED_REQUESTS = 0


class Server(object):
    """A simple server.

    Server with configurable exponential serving rate.
    """

    def __init__(self, env, serving_rate):
        self._env = env
        self._serving_rate = serving_rate

    @property
    def serving_time(self):
        """Exponential serving time based on serving ratio."""
        return numpy.random.exponential(1.0 / self._serving_rate)

    def serve(self):
        """Serve and count the amount of requests completed."""
        global SERVED_REQUESTS
        yield self._env.timeout(self.serving_time)
        SERVED_REQUESTS += 1
