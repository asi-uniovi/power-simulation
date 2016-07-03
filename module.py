"""Module for the dependency injection binding."""

import os
import sqlite3

import injector

from configuration import Configuration
from singleton import Singleton
from static import KB, MB


class Binder(injector.Module, metaclass=Singleton):
    """This binds all the types needed on the simulation."""

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
        conn.execute('PRAGMA cache_size = %d;' % -int(MB(64) / KB(1)))
        conn.execute('PRAGMA synchronous = OFF;')
        conn.execute('PRAGMA temp_store = MEMORY;')
        return conn


class CustomInjector(injector.Injector, metaclass=Singleton):
    """This is just a singleton Injector."""
