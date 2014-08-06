#!/usr/bin/env python3

"""A very simple simuation of a 1/M/c queuing system."""

import numpy
import simpy
import sys

REQUESTS = 0
SERVED_REQUESTS = 0
WAITING_TIME = 0.0


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


class Request(object):
    """A request from the user.

    Asks for a server by waiting in the queue and then places the request.
    """

    def __init__(self, env, queue, serving_rate):
        global REQUESTS
        self._env = env
        self._queue = queue
        self._serving_rate = serving_rate
        REQUESTS += 1

    def run(self):
        """Waits for a place in the queue and makes the request."""
        global WAITING_TIME
        with self._queue.request() as req:
            arrival_time = self._env.now
            yield req
            WAITING_TIME += self._env.now - arrival_time
            yield self._env.process(Server(self._env,
                                           self._serving_rate).serve())


class User(object):
    """A user model.

    This class generates requests to the system randomly, based on:
      - A distribution of arrival times: defaults to exponential.
      - The average interarrival time.
    """

    def __init__(self, env, mean_interarrival_time, server):
        self._env = env
        self._mean_interarrival_time = mean_interarrival_time
        self._server = server

    @property
    def interarrival_time(self):
        return numpy.random.exponential(self._mean_interarrival_time)

    def run(self):
        """Generates requests af the defined frequency."""
        while True:
            self._env.process(Request(self._env, self._server, 4.0).run())
            yield self._env.timeout(self.interarrival_time)


def main():
    """Constructs the system and runs the simulation."""
    env = simpy.Environment()
    servers = simpy.Resource(env, capacity=1)
    env.process(User(env, 0.25, servers).run())
    env.run(until=10000)
    print('Total requests: %d' % REQUESTS)
    print('Mean waiting time: %f' % (WAITING_TIME / REQUESTS))
    print('Served requests: %d' % SERVED_REQUESTS)


if __name__ == '__main__':
    sys.exit(main())
