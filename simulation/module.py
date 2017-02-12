"""Module for the dependency injection binding."""

import os
import sqlite3
import injector
from simulation.configuration import Configuration
from simulation.static import KB, MB


class Module(injector.Module):
    """This binds all the types needed on the simulation."""

    @injector.singleton
    @injector.provider
    @injector.inject
    # pylint: disable=no-self-use
    def provide_connection(self, config: Configuration) -> sqlite3.Connection:
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
