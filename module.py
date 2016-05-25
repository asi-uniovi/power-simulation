"""Module for the dependency injection binding."""

import os
import sqlite3

import injector
import simpy

from configuration import Configuration
from singleton import Singleton
from static import KB, MB


env_key = injector.Key('env')  # pylint: disable=invalid-name


class Binder(injector.Module, metaclass=Singleton):
    """This binds all the types needed on the simulation."""

    def __init__(self):
        super(Binder, self).__init__()
        self._env = simpy.Environment()

    def configure(self, binder):
        """Sets the basic configuration and dependency injections."""
        binder.bind(env_key, to=injector.InstanceProvider(self._env))

    @injector.singleton
    @injector.provides(sqlite3.Connection)
    @injector.inject(config=Configuration)
    # pylint: disable=no-self-use
    def provide_db_connection(self, config):
        """Sets the database up for the module to work."""
        db_name = config.get_config('database_name', 'stats')
        try:
            os.remove(db_name)
        except FileNotFoundError:
            pass
        conn = sqlite3.connect(db_name)
        conn.isolation_level = None
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode = OFF;')
        conn.execute('PRAGMA foreign_keys = OFF;')
        conn.execute('PRAGMA cache_size = %d;' % -int(MB(512) / KB(1)))
        conn.execute('PRAGMA synchronous = OFF;')
        conn.execute('PRAGMA temp_store = MEMORY;')
        return conn


class CustomInjector(injector.Injector, metaclass=Singleton):
    """This is just a singleton Injector."""
