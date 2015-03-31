"""Module for the dependency injection binding."""

import injector
import simpy
import six

from singleton import Singleton

config_key = injector.Key('config')  # pylint: disable=invalid-name
env_key = injector.Key('env')  # pylint: disable=invalid-name


class Binder(six.with_metaclass(Singleton, injector.Module)):
    """This binds all the types needed on the simulation."""

    def __init__(self, config=None):
        """config is optional to allow second constructions."""
        self._config = config
        self._env = simpy.Environment()

    def configure(self, binder):
        """Sets the basic configuration and dependency injections."""
        binder.bind(config_key, to=injector.InstanceProvider(self._config))
        binder.bind(env_key, to=injector.InstanceProvider(self._env))


class CustomInjector(six.with_metaclass(Singleton, injector.Injector)):
    """This is just a singleton Injector."""
