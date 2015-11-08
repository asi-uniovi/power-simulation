"""Database backed histogram."""

import array
import collections
import gc
import injector
import numpy
import sqlite3

from base import Base
from static import WEEK


class Histogram(Base):
    """Histogram stored in a DB."""

    @injector.inject(conn=sqlite3.Connection)
    def __init__(self, conn, name):
        super(Histogram, self).__init__()
        self.__name = name
        self.__cursor = conn.cursor()
        self.__write_cache_ts = array.array('f')
        self.__write_cache_val = array.array('f')

    def append(self, timestamp, value):
        """Inserts into the histogram, just in cache for now."""
        self.__write_cache_ts.append(timestamp)
        self.__write_cache_val.append(value)
        if len(self.__write_cache_ts) > self.get_config_int('cache_size',
                                                            section='stats'):
            self.flush()

    def flush(self):
        """Dump the cache to the database."""
        self.__cursor.executemany(
            ('INSERT INTO histogram(histogram, timestamp, value) '
             "VALUES('%s', ?, ?);") % self.__name,
            zip(self.__write_cache_ts, self.__write_cache_val))
        self.__write_cache_ts = array.array('f')
        self.__write_cache_val = array.array('f')
        gc.collect()

    def get_hourly_histogram(self, hour):
        """Gets the subhistogram for one particular hour."""
        self.flush()
        self.__cursor.execute(
            '''SELECT value
                 FROM histogram
                WHERE histogram = ?
                      AND hour = ?;''',
            (self.__name, hour))
        return numpy.asarray(self.__cursor.fetchall())


@injector.inject(conn=sqlite3.Connection)
def create_histogram_tables(conn):
    """Creates the tables on the database."""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS histogram (
          id        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
          hour      INTEGER,
          histogram TEXT    NOT NULL,
          timestamp REAL    NOT NULL,
          value     REAL    NOT NULL
        );''')
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS i_histogram ON histogram(histogram, hour);')
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS t_hour AFTER INSERT ON histogram
        FOR EACH ROW BEGIN
          UPDATE histogram SET hour =
              (CAST(new.timestamp AS INTEGER) %% %d) / 3600
            WHERE id = NEW.id;
        END;''' % WEEK(1))
    cursor.execute('DELETE FROM histogram;')
    cursor.execute('VACUUM;')
