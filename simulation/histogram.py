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
import logging
import operator
import typing
import sqlite3
import injector
import numpy
from simulation.base import Base
from simulation.static import WEEK

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Histogram(Base):
    """Histogram stored in a DB."""
    __run = 0

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

    @classmethod
    def new_run(cls):
        """Increment the run counter."""
        cls.__run += 1

    @classmethod
    def runs(cls):
        """Indicates the number of runs."""
        return cls.__run

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
            logger.debug('Histogram is being flushed with %d elements.',
                         len(self.__write_cache))
            self.__cursor.executemany(
                '''INSERT INTO histogram
                       (run, histogram, timestamp, computer, value)
                   VALUES(%d, '%s', ?, ?, ?);''' % (self.runs(), self.__name),
                self.__write_cache)
            self.__write_cache = []

    def get_all_hourly_histograms(
            self, run: int = None) -> typing.List[numpy.ndarray]:
        """Gets all the subhistograms per hour."""
        if run is None:
            run = self.runs()
        self.flush()
        self.__cursor.execute(
            '''SELECT hour, value
                 FROM histogram
                WHERE histogram = ?
                      AND run = ?
             ORDER BY hour ASC;''',
            (self.__name, run))
        dct = {i: numpy.ascontiguousarray([i[1] for i in g])
               for i, g in itertools.groupby(
                   self.__cursor.fetchall(), operator.itemgetter(0))}
        return [dct.get(i, numpy.asarray([])) for i in range(168)]

    def get_all_histogram(
            self, cid: str = None, run: int = None) -> numpy.ndarray:
        """Gets all the data from the histogram."""
        if run is None:
            run = self.runs()
        self.flush()
        if cid is None:
            self.__cursor.execute(
                '''SELECT value
                     FROM histogram
                    WHERE histogram = ?
                          AND run = ?;''',
                (self.__name, run))
        else:
            self.__cursor.execute(
                '''SELECT value
                     FROM histogram
                    WHERE histogram = ?
                          AND computer = ?
                          AND run = ?;''',
                (self.__name, cid, run))
        return numpy.ascontiguousarray(
            [i['value'] for i in self.__cursor.fetchall()])

    def get_all_hourly_summaries(
            self, run: int = None) -> typing.List[typing.Dict[str, float]]:
        """Gets all the summaries per hour."""
        if run is None:
            run = self.runs()
        ret = []
        for hist in self.get_all_hourly_histograms(run):
            dct = {}
            for summary in ('mean', 'median'):
                try:
                    dct[summary] = getattr(numpy, summary)(hist)
                except (IndexError, RuntimeWarning):
                    dct[summary] = 0.0
            ret.append(dct)
        return ret

    def get_all_hourly_count(self, run: int = None) -> typing.List[int]:
        """Gets all the count per hour."""
        if run is None:
            run = self.runs()
        self.flush()
        self.__cursor.execute(
            '''SELECT hour, COUNT(*) AS count
                 FROM histogram
                WHERE histogram = ?
                      AND run = ?
             GROUP BY hour
             ORDER BY hour ASC;''',
            (self.__name, run))
        dct = dict(self.__cursor.fetchall())
        return [dct.get(i, 0) for i in range(168)]

    def sum_histogram(self, cid: str = None, run: int = None) -> int:
        """Sums up all the elements of this histogram."""
        if cid is None:
            return self.__sum
        if run is None:
            run = self.runs()
        self.flush()
        self.__cursor.execute(
            '''SELECT SUM(value) AS sum
                 FROM histogram
                WHERE histogram = ?
                      AND computer = ?
                      AND run = ?;''',
            (self.__name, cid, run))
        return int(self.__cursor.fetchone()['sum'])

    def count_histogram(self, cid: str = None, run: int = None) -> int:
        """Counts the number of elements in this histogram."""
        if cid is None:
            return self.__count
        if run is None:
            run = self.runs()
        self.flush()
        self.__cursor.execute(
            '''SELECT COUNT(*) AS count
                 FROM histogram
                WHERE histogram = ?
                      AND computer = ?
                      AND run = ?;''',
            (self.__name, cid, run))
        return int(self.__cursor.fetchone()['count'])


def create_histogram_tables(conn: sqlite3.Connection) -> None:
    """Creates the tables on the database."""
    cursor = conn.cursor()
    cursor.execute('DROP TRIGGER IF EXISTS t_hour;')
    cursor.execute('DROP INDEX IF EXISTS i_histogram_hour;')
    cursor.execute('DROP TABLE IF EXISTS histogram;')
    cursor.execute('''
        CREATE TABLE histogram (
          id        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
          run       INTEGER NOT NULL,
          hour      INTEGER,
          histogram TEXT    NOT NULL,
          computer  TEXT    NOT NULL,
          timestamp REAL    NOT NULL,
          value     REAL    NOT NULL
        );''')
    cursor.execute(
        'CREATE INDEX i_hist_run ON histogram(histogram, run);')
    cursor.execute(
        'CREATE INDEX i_comp_run ON histogram(computer, run);')
    cursor.execute(
        'CREATE INDEX i_hist_comp_run ON histogram(histogram, computer, run);')
    cursor.execute(
        'CREATE INDEX i_hour ON histogram(hour);')
    cursor.execute('''
        CREATE TRIGGER t_hour AFTER INSERT ON histogram
        FOR EACH ROW BEGIN
          UPDATE histogram SET hour =
              (CAST(new.timestamp AS INTEGER) %% %d) / 3600
            WHERE id = NEW.id;
        END;''' % WEEK(1))
