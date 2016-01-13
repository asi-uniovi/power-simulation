"""Database backed histogram."""

import array
import gc
import injector
import itertools
import numpy
import operator
import sqlite3

try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

from base import Base
from static import WEEK


class Histogram(Base):
    """Histogram stored in a DB."""

    @injector.inject(conn=sqlite3.Connection)
    def __init__(self, conn, name):
        super(Histogram, self).__init__()
        self.__cursor = conn.cursor()
        self.__name = name
        self.__write_cache_ts = array.array('f')
        self.__write_cache_val = array.array('f')

    def append(self, timestamp, value):
        """Inserts into the histogram, just in cache for now."""
        self.__write_cache_ts.append(timestamp)
        self.__write_cache_val.append(value)
        if (len(self.__write_cache_ts)
                >= self.get_config_int('cache_size', section='stats')):
            self.flush()
        assert len(self.__write_cache_ts) == len(self.__write_cache_val)

    def flush(self):
        """Dump the cache to the database."""
        if len(self.__write_cache_ts) > 0:
            self.__cursor.executemany(
                ('INSERT INTO histogram(histogram, timestamp, value) '
                 "VALUES('%s', ?, ?);") % self.__name,
                zip(self.__write_cache_ts, self.__write_cache_val))
            self.__write_cache_ts = array.array('f')
            self.__write_cache_val = array.array('f')
            Histogram.__cache_invalidate()
            gc.collect()
        assert len(self.__write_cache_ts) == len(self.__write_cache_val)

    @lru_cache()
    def get_all_hourly_histograms(self):
        """Gets all the subhistograms per hour."""
        self.flush()
        self.__cursor.execute(
            '''SELECT hour, value
                 FROM histogram
                WHERE histogram = ?
             ORDER BY hour ASC;''',
            (self.__name,))
        return self.__fetch_hourly()

    @lru_cache()
    def get_all_hourly_summaries(self, summaries):
        """Gets all the summaries per hour."""
        l = []
        for h in self.get_all_hourly_histograms():
            d = {}
            for s in summaries:
                try:
                    d[s] = getattr(numpy, s)(h)
                except (IndexError, RuntimeWarning):
                    d[s] = 0
            l.append(d)
        return l

    @lru_cache()
    def get_all_hourly_count(self):
        """Gets all the count per hour."""
        self.flush()
        self.__cursor.execute(
            '''SELECT hour, COUNT(*) AS count
                 FROM histogram
                WHERE histogram = ?
             GROUP BY hour
             ORDER BY hour ASC;''',
            (self.__name,))
        d = dict(self.__cursor.fetchall())
        return [d.get(i, 0) for i in range(168)]

    def __fetch_hourly(self):
        """Groups by hour and fills in the hours with no data."""
        d = {i: numpy.asarray(list(i[1] for i in g))
             for i, g in itertools.groupby(
                 self.__cursor.fetchall(), operator.itemgetter(0))}
        return [d.get(i, []) for i in range(168)]

    @classmethod
    def __cache_invalidate(cls):
        """Invalidates all the memoizing caches."""
        cls.get_all_hourly_histograms.cache_clear()
        cls.get_all_hourly_summaries.cache_clear()
        cls.get_all_hourly_count.cache_clear()


@injector.inject(conn=sqlite3.Connection)
def create_histogram_tables(conn):
    """Creates the tables on the database."""
    cursor = conn.cursor()
    cursor.execute('DROP TRIGGER IF EXISTS t_hour;')
    cursor.execute('DROP INDEX IF EXISTS i_histogram_hour;')
    cursor.execute('DROP TABLE IF EXISTS histogram;')
    cursor.execute('''
        CREATE TABLE histogram (
          id        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
          hour      INTEGER,
          histogram TEXT    NOT NULL,
          timestamp REAL    NOT NULL,
          value     REAL    NOT NULL
        );''')
    cursor.execute(
        'CREATE INDEX i_histogram_hour ON histogram(histogram, hour);')
    cursor.execute('''
        CREATE TRIGGER t_hour AFTER INSERT ON histogram
        FOR EACH ROW BEGIN
          UPDATE histogram SET hour =
              (CAST(new.timestamp AS INTEGER) %% %d) / 3600
            WHERE id = NEW.id;
        END;''' % WEEK(1))
