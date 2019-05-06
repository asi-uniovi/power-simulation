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
from simulation.activity_distribution import DistributionFactory
from simulation.base import Base
from simulation.static import hour_to_day
from simulation.static import WEEK

logger = logging.getLogger(__name__)


class Histogram(Base):
    """Histogram stored in a DB."""

    @injector.inject
    @injector.noninjectable('name')
    def __init__(self, distr_factory: DistributionFactory,
                 conn: sqlite3.Connection, name: str):
        super(Histogram, self).__init__()
        self.__activity_distribution = distr_factory()
        self.__cache_size = self.get_config_int('cache_size', section='stats')
        self.__cursor = conn.cursor()
        self.__name = name
        self.__write_cache = []

    @property
    def servers(self) -> int:
        """Number of servers being simulated."""
        return len(self.__activity_distribution.servers)

    def append(self, timestamp: int, cid: str, value: float) -> None:
        """Inserts into the histogram, just in cache for now."""
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
                   VALUES(%d, '%s', ?, ?, ?);''' % (self.runs, self.__name),
                self.__write_cache)
            self.__write_cache = []

    def get_all_hourly_histograms(
            self, run: int = None) -> typing.List[numpy.ndarray]:
        """Gets all the subhistograms per hour."""
        if run is None:
            run = self.runs
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

    def get_all_events(
            self, cid: str = None, run: int = None
    ) -> typing.List[typing.Tuple[float, float]]:
        """Gets all the data from the histogram."""
        if run is None:
            run = self.runs
        self.flush()
        if cid is None:
            self.__cursor.execute(
                '''SELECT timestamp, value
                     FROM histogram
                    WHERE histogram = ?
                          AND run = ?;''',
                (self.__name, run))
        else:
            self.__cursor.execute(
                '''SELECT timestamp, value
                     FROM histogram
                    WHERE histogram = ?
                          AND run = ?
                          AND computer = ?;''',
                (self.__name, run, cid))
        return [(i['timestamp'], i['value']) for i in self.__cursor.fetchall()]

    def get_all_histogram(
            self, cid: str = None, run: int = None) -> numpy.ndarray:
        """Returns all the histogram values."""
        return numpy.asarray([i for _, i in self.get_all_events(cid, run)])

    def get_all_hourly_percentiles(
            self, percentile: float, run: int = None) -> typing.List[float]:
        """Gets all the summaries per hour."""
        if run is None:
            run = self.runs
        percentiles = []
        for hist in self.get_all_hourly_histograms(run):
            try:
                percentiles.append(numpy.percentile(hist, percentile))
            except IndexError:
                percentiles.append(0.0)
        return percentiles

    def get_all_hourly_count(self, run: int = None) -> typing.List[int]:
        """Gets all the count per hour."""
        if run is None:
            run = self.runs
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
        total = [dct.get(i, 0) / self.simulation_weeks
                 for i in range(168)]
        if not self.get_arg('per_hour'):
            total = [i / 168 for i in total]
        if not self.get_arg('per_pc'):
            total = [i / self.servers for i in total]
        return total

    def get_all_hourly_distributions(self, run: int = None):
        """Returns all the intervals per hour."""
        if run is None:
            run = self.runs
        self.flush()
        self.__cursor.execute(
            '''SELECT hour, value
                 FROM histogram
                WHERE histogram = ?
                      AND run = ?
             ORDER BY hour ASC;''',
            (self.__name, run))
        transposed = {}
        for timestamp, intervals in itertools.groupby(
                self.__cursor.fetchall(), operator.itemgetter(0)):
            day, hour = hour_to_day(int(timestamp))
            transposed.setdefault(day, {}).setdefault(
                hour, numpy.asarray([i for _, i in intervals]))
        return transposed

    def sum_histogram(
            self, cid: str = None, trim: bool = False, run: int = None) -> int:
        """Sums up all the elements of this histogram."""
        if run is None:
            run = self.runs
        self.flush()
        if trim:
            if cid is None:
                self.__cursor.execute(
                    '''SELECT SUM(v) AS sum
                         FROM (SELECT CASE
                                          WHEN timestamp + value > %d
                                          THEN %d - timestamp
                                          ELSE value
                                      END AS v
                                 FROM histogram
                                WHERE histogram = ?
                                      AND run = ?);''' % (
                                          self.simulation_time,
                                          self.simulation_time),
                    (self.__name, run))
            else:
                self.__cursor.execute(
                    '''SELECT SUM(v) AS sum
                         FROM (SELECT CASE
                                          WHEN timestamp + value > %d
                                          THEN %d - timestamp
                                          ELSE value
                                      END AS v
                                 FROM histogram
                                WHERE histogram = ?
                                      AND run = ?
                                      AND computer = ?);''' % (
                                          self.simulation_time,
                                          self.simulation_time),
                    (self.__name, run, cid))
        else:
            if cid is None:
                self.__cursor.execute(
                    '''SELECT SUM(value) AS sum
                         FROM histogram
                        WHERE histogram = ?
                              AND run = ?;''',
                    (self.__name, run))
            else:
                self.__cursor.execute(
                    '''SELECT SUM(value) AS sum
                         FROM histogram
                        WHERE histogram = ?
                              AND run = ?
                              AND computer = ?;''',
                    (self.__name, run, cid))

        return int(self.__cursor.fetchone()['sum'])

    def count_histogram(self, cid: str = None, run: int = None) -> int:
        """Counts the number of elements in this histogram."""
        if run is None:
            run = self.runs
        self.flush()
        if cid is None:
            self.__cursor.execute(
                '''SELECT COUNT(*) AS count
                     FROM histogram
                    WHERE histogram = ?
                          AND run = ?;''',
                (self.__name, run))
        else:
            self.__cursor.execute(
                '''SELECT COUNT(*) AS count
                     FROM histogram
                    WHERE histogram = ?
                          AND run = ?
                          AND computer = ?;''',
                (self.__name, run, cid))
        return int(self.__cursor.fetchone()['count'])


def create_histogram_tables(conn: sqlite3.Connection) -> None:
    """Creates the tables on the database."""
    cursor = conn.cursor()
    cursor.execute('DROP TRIGGER IF EXISTS t_hour;')
    cursor.execute('DROP INDEX IF EXISTS i_hist_run_comp;')
    cursor.execute('DROP INDEX IF EXISTS i_hist_run_hour;')
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
        'CREATE INDEX i_hist_run_hour ON histogram(histogram, run, hour);')
    cursor.execute(
        'CREATE INDEX i_hist_run_comp ON histogram(histogram, run, computer);')
    cursor.execute('''
        CREATE TRIGGER t_hour AFTER INSERT ON histogram
        FOR EACH ROW BEGIN
          UPDATE histogram SET hour =
              (CAST(new.timestamp AS INTEGER) %% %d) / 3600
            WHERE id = NEW.id;
        END;''' % WEEK(1))
