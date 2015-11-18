"""Module for the dependency injection binding."""

import injector
import simpy
import six
import sqlite3

from singleton import Singleton
from static import KB, MB

config_key = injector.Key('config')
env_key = injector.Key('env')


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

    @injector.singleton
    @injector.provides(sqlite3.Connection)
    @injector.inject(config=config_key)
    def provide_db_connection(self, config):
        """Sets the database up for the module to work."""
        conn = sqlite3.connect(config.get('stats', 'database_name'))
        conn.isolation_level = None
        conn.row_factory = sqlite3.Row
        conn.enable_load_extension(True)
        conn.execute('PRAGMA journal_mode = OFF;')
        conn.execute('PRAGMA foreign_keys = OFF;')
        conn.execute('PRAGMA cache_size = %d;' % -int(MB(128) / KB(1)))
        conn.execute('PRAGMA synchronous = OFF;')
        conn.execute('PRAGMA temp_store = MEMORY;')
        return conn


class CustomInjector(six.with_metaclass(Singleton, injector.Injector)):
    """This is just a singleton Injector."""
