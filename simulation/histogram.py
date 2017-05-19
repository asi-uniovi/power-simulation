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

"""Database backed histogram."""

import itertools
import operator
import typing
import sqlite3
import injector
import numpy
from simulation.base import Base
from simulation.static import WEEK


class Histogram(Base):
    """Histogram stored in a DB."""

    @injector.inject
    @injector.noninjectable('name')
    def __init__(self, conn: sqlite3.Connection, name: str):
        super(Histogram, self).__init__()
        self.__cache_size = self.get_config_int('cache_size', section='stats')
        self.__cursor = conn.cursor()
        self.__name = name
        self.__sum = 0
        self.__count = 0
        self.__write_cache = []

    def append(self, timestamp: int, cid: str, value: float) -> None:
        """Inserts into the histogram, just in cache for now."""
        self.__sum += value
        self.__count += 1
        self.__write_cache.append((timestamp, cid, float(value)))
        if len(self.__write_cache) >= self.__cache_size:
            self.flush()

    def flush(self) -> None:
        """Dump the cache to the database."""
        if self.__write_cache:
            self.__cursor.executemany(
                ('INSERT INTO histogram(histogram, timestamp, computer, value) '
                 "VALUES('%s', ?, ?, ?);") % self.__name, self.__write_cache)
            self.__write_cache = []

    def truncate(self) -> None:
        """Deletes all the data from the table."""
        self.__sum = 0
        self.__count = 0
        self.__write_cache = []
        self.__cursor.execute('DELETE FROM histogram WHERE histogram = ?;',
                              (self.__name,))
        self.__cursor.execute('VACUUM;')

    def get_all_hourly_histograms(self) -> typing.List[numpy.ndarray]:
        """Gets all the subhistograms per hour."""
        self.flush()
        self.__cursor.execute(
            '''SELECT hour, value
                 FROM histogram
                WHERE histogram = ?
             ORDER BY hour ASC;''',
            (self.__name,))
        dct = {i: numpy.ascontiguousarray([i[1] for i in g])
               for i, g in itertools.groupby(
                   self.__cursor.fetchall(), operator.itemgetter(0))}
        return [dct.get(i, []) for i in range(168)]

    def get_all_histogram(self, cid: str = None) -> numpy.ndarray:
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

    def get_all_hourly_summaries(self) -> typing.List[typing.Dict[str, float]]:
        """Gets all the summaries per hour."""
        ret = []
        for hist in self.get_all_hourly_histograms():
            dct = {}
            for summary in ('mean', 'median'):
                try:
                    dct[summary] = getattr(numpy, summary)(hist)
                except (IndexError, RuntimeWarning):
                    dct[summary] = 0.0
            ret.append(dct)
        return ret

    def get_all_hourly_count(self) -> typing.List[int]:
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

    def sum_histogram(self, cid: str = None) -> int:
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

    def count_histogram(self, cid: str = None) -> int:
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


def create_histogram_tables(conn: sqlite3.Connection):
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
