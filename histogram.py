"""Database backed histogram."""

import functools
import itertools
import operator
import sqlite3

import injector
import numpy

from base import Base
from static import WEEK


class Histogram(Base):
    """Histogram stored in a DB."""

    @injector.inject(conn=sqlite3.Connection)
    def __init__(self, conn, name):
        super(Histogram, self).__init__()
        self.__cache_size = self.get_config_int('cache_size', section='stats')
        self.__cursor = conn.cursor()
        self.__name = name
        self.__sum = 0
        self.__count = 0
        self.__write_cache = []

    def append(self, timestamp, cid, value):
        """Inserts into the histogram, just in cache for now."""
        self.__sum += value
        self.__count += 1
        self.__write_cache.append((timestamp, cid, float(value)))
        if len(self.__write_cache) >= self.__cache_size:
            self.flush()

    def flush(self):
        """Dump the cache to the database."""
        if len(self.__write_cache) > 0:
            self.__cursor.executemany(
                ('INSERT INTO histogram(histogram, timestamp, computer, value) '
                 "VALUES('%s', ?, ?, ?);") % self.__name, self.__write_cache)
            self.__write_cache = []
            Histogram.__cache_invalidate()

    @functools.lru_cache(maxsize=1)
    def get_all_hourly_histograms(self):
        """Gets all the subhistograms per hour."""
        self.flush()
        self.__cursor.execute(
            '''SELECT hour, value
                 FROM histogram
                WHERE histogram = ?
             ORDER BY hour ASC;''',
            (self.__name,))
        return self.__fetch_hourly_array()

    @functools.lru_cache()
    def get_all_histogram(self, cid=None):
        """Gets all the data from the histogram."""
        self.flush()
        if cid is None:
            self.__cursor.execute(
                '''SELECT value
                     FROM histogram
                    WHERE histogram = ?;''',
                (self.__name,))
        else:
            self.__cursor.execute(
                '''SELECT value
                     FROM histogram
                    WHERE histogram = ?
                          AND computer = ?;''',
                (self.__name, cid))
        return numpy.ascontiguousarray(
            [i['value'] for i in self.__cursor.fetchall()])

    @functools.lru_cache()
    def get_all_hourly_summaries(self):
        """Gets all the summaries per hour."""
        self.flush()
        self.__cursor.execute(
            '''SELECT hour, AVG(value) AS mean, MEDIAN(value) AS median
                 FROM histogram
                WHERE histogram = ?
             GROUP BY hour
             ORDER BY hour ASC;''',
            (self.__name,))
        dct = {i['hour']: i for i in self.__cursor.fetchall()}
        return [dct.get(i, {'mean': 0.0, 'median': 0.0}) for i in range(168)]

    @functools.lru_cache()
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
        dct = dict(self.__cursor.fetchall())
        return [dct.get(i, 0) for i in range(168)]

    def sum_histogram(self, cid=None):
        """Sums up all the elements of this histogram."""
        if cid is None:
            return self.__sum
        self.flush()
        self.__cursor.execute(
            '''SELECT SUM(value) AS sum
                 FROM histogram
                WHERE histogram = ?
                      AND computer = ?;''',
            (self.__name, cid))
        return int(self.__cursor.fetchone()['sum'])

    def count_histogram(self, cid=None):
        """Counts the number of elements in this histogram."""
        if cid is None:
            return self.__count
        self.flush()
        self.__cursor.execute(
            '''SELECT COUNT(*) AS count
                 FROM histogram
                WHERE histogram = ?
                      AND computer = ?;''',
            (self.__name, cid))
        return int(self.__cursor.fetchone()['count'])

    def __fetch_hourly_array(self):
        """Groups by hour and fills in the hours with no data."""
        dct = {i: numpy.asarray(list(i[1] for i in g))
               for i, g in itertools.groupby(
                   self.__cursor.fetchall(), operator.itemgetter(0))}
        return [dct.get(i, []) for i in range(168)]

    @classmethod
    def __cache_invalidate(cls):
        """Invalidates all the memoizing caches."""
        # pylint: disable=no-member
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
          computer  TEXT    NOT NULL,
          timestamp REAL    NOT NULL,
          value     REAL    NOT NULL
        );''')
    cursor.execute(
        'CREATE INDEX i_histogram ON histogram(histogram);')
    cursor.execute(
        'CREATE INDEX i_computer ON histogram(computer);')
    cursor.execute(
        'CREATE INDEX i_hour ON histogram(hour);')
    cursor.execute('''
        CREATE TRIGGER t_hour AFTER INSERT ON histogram
        FOR EACH ROW BEGIN
          UPDATE histogram SET hour =
              (CAST(new.timestamp AS INTEGER) %% %d) / 3600
            WHERE id = NEW.id;
        END;''' % WEEK(1))
