# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
