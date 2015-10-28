"""Database backed histogram."""

import array
import injector
import sqlite3

MAX_ENTRIES = 1000000  # TODO(m3drano): Move this into the config file.


class Histogram(object):
    """Histogram stored in a DB."""

    def __init__(self, name, cursor, dimension=7*24):
        super(Histogram, self).__init__()
        self.__name = name
        self.__dimension = dimension
        self.__cursor = cursor
        self.__write_cache_ts = array.array('f')
        self.__write_cache_val = array.array('f')
        self.__create_entries()

    def append(self, timestamp, value):
        """Inserts into the histogram, just in cache for now."""
        self.__write_cache_ts.append(float(timestamp))
        self.__write_cache_val.append(float(value))
        if len(self.__write_cache_ts) > MAX_ENTRIES:
            self.flush()

    def flush(self):
        """Dump the cache to the database."""
        self.__cursor.executemany(
            ('INSERT INTO histogram_entry(histogram, timestamp, value) '
             "VALUES('%s', ?, ?);") % self.__name,
            zip(self.__write_cache_ts, self.__write_cache_val))
        self.__write_cache_ts = array.array('f')
        self.__write_cache_val = array.array('f')

    def get_hourly_histogram(self, hour):
        """Gets the subhistogram for one particular hour."""
        self.flush()
        self.__cursor.execute(
            '''SELECT value
                 FROM histogram_entry
                WHERE histogram = ?
                      AND ((timestamp % ?) / 3600) = ?;''',
            (self.__name, self.__dimension * 3600, hour))
        return [i[0] for i in self.__cursor.fetchall()]

    def get_hourly_statistics(self):
        """Calculate all statistics for the histogram per hour."""
        self.flush()
        self.__cursor.execute(
            '''SELECT (timestamp % ?) / 3600 AS hour,
                      COUNT(value) AS count,
                      SUM(value) AS sum,
                      AVG(value) AS mean,
                      STDEV(value) AS stdev,
                      MEDIAN(value) AS median,
                      MIN(value) AS min,
                      MAX(value) AS max,
                      MODE(value) AS mode
                 FROM histogram_entry
                WHERE histogram = ?
             GROUP BY hour
             ORDER BY hour;''',
            (self.__dimension * 3600, self.__name))
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
                 FROM histogram_entry
                WHERE histogram = ?;''',
            (self.__name,))
        return self.__cursor.fetchone()

    def dump_to_file(self, filename):
        """Dumps a histogram viriable to a file."""
        raise NotImplementedError

    def __create_entries(self):
        """Sets the entries for this histogram."""
        self.__cursor.execute(
            'INSERT OR REPLACE INTO histogram(name, dimension) '
            'VALUES(?, ?);', (self.__name, self.__dimension))


@injector.inject(conn=sqlite3.Connection)
def create_histogram_tables(conn):
    """Creates the tables on the database."""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS histogram (
          name       TEXT    NOT NULL PRIMARY KEY,
          dimension  INTEGER NOT NULL DEFAULT 168
        );''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS histogram_entry (
          id        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
          histogram TEXT    NOT NULL REFERENCES histogram(name),
          timestamp REAL    NOT NULL,
          value     REAL    NOT NULL
        );''')
    cursor.execute('DELETE FROM histogram_entry;')
    cursor.execute('DELETE FROM histogram;')
    cursor.execute('VACUUM;')
