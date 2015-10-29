"""Database backed histogram."""

import array
import injector
import sqlite3

from static import WEEK

MAX_ENTRIES = 1000000  # TODO(m3drano): Move this into the config file.


class Histogram(object):
    """Histogram stored in a DB."""

    def __init__(self, name, cursor):
        super(Histogram, self).__init__()
        self.__name = name
        self.__cursor = cursor
        self.__write_cache_ts = array.array('f')
        self.__write_cache_val = array.array('f')

    def append(self, timestamp, value):
        """Inserts into the histogram, just in cache for now."""
        self.__write_cache_ts.append(timestamp)
        self.__write_cache_val.append(value)
        if len(self.__write_cache_ts) > MAX_ENTRIES:
            self.flush()

    def flush(self):
        """Dump the cache to the database."""
        self.__cursor.executemany(
            ('INSERT INTO histogram(histogram, timestamp, value) '
             "VALUES('%s', ?, ?);") % self.__name,
            zip(self.__write_cache_ts, self.__write_cache_val))
        self.__write_cache_ts = array.array('f')
        self.__write_cache_val = array.array('f')

    def get_hourly_histogram(self, hour):
        """Gets the subhistogram for one particular hour."""
        self.flush()
        self.__cursor.execute(
            '''SELECT value
                 FROM histogram
                WHERE histogram = ?
                      AND hour = ?;''',
            (self.__name, hour))
        return [i[0] for i in self.__cursor.fetchall()]

    def get_hourly_statistics(self):
        """Calculate all statistics for the histogram per hour."""
        self.flush()
        self.__cursor.execute(
            '''SELECT hour,
                      COUNT(value) AS count,
                      SUM(value) AS sum,
                      AVG(value) AS mean,
                      STDEV(value) AS stdev,
                      MEDIAN(value) AS median,
                      MIN(value) AS min,
                      MAX(value) AS max,
                      MODE(value) AS mode
                 FROM histogram
                WHERE histogram = ?
             GROUP BY hour
             ORDER BY hour;''',
            (self.__name,))
        return self.__cursor.fetchall()

    def get_statistics(self):
        """Calculate all statistics for the histogram."""
        self.flush()
        self.__cursor.execute(
            '''SELECT COUNT(value) AS count,
                      SUM(value) AS sum,
                      AVG(value) AS mean,
                      STDEV(value) AS stdev,
                      MEDIAN(value) AS median,
                      MIN(value) AS min,
                      MAX(value) AS max,
                      MODE(value) AS mode
                 FROM histogram
                WHERE histogram = ?;''',
            (self.__name,))
        return self.__cursor.fetchone()

    def dump_to_file(self, filename):
        """Dumps a histogram viriable to a file."""
        raise NotImplementedError


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
        'CREATE INDEX IF NOT EXISTS i_histogram ON histogram(histogram);')
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS t_hour AFTER INSERT ON histogram
        FOR EACH ROW BEGIN
          UPDATE histogram SET hour =
              (CAST(new.timestamp AS INTEGER) %% %d) / 3600
            WHERE id = NEW.id;
        END;''' % WEEK(1))
    cursor.execute('DELETE FROM histogram;')
    cursor.execute('VACUUM;')
