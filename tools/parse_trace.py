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

"""Common tooling for parsing traces."""

import itertools
import json
import operator
from simulation.static import DAYS


def parse_model(traces, day=None, hour=None):
    """Parses the model for a given trace."""
    models = {}
    for t, data in traces.items():
        for d in data:
            if (day is None or hour is None
                    or (DAYS[d['Day']] == day and int(d['Hour']) == hour)):
                models.setdefault(t, []).extend(d['Intervals'])
    return models


def parse_trace(trace_file, day=None, hour=None):
    """Parses the trace file to get a list of inactivity intervals."""
    with open(trace_file) as trace:
        trace = [i for i in json.load(trace) if i['PC'] != '_Total']
        key = operator.itemgetter('PC')
        models = {}  # PC > key > intervals (list)
        for pc, trace in itertools.groupby(sorted(trace, key=key), key=key):
            models[pc] = parse_model(
                {t['Type']: t['data'] for t in trace}, day, hour)
        return models
