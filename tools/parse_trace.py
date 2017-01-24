"""Common tooling for parsing traces."""

import itertools
import json
import operator


# pylint: disable=invalid-name
def parse_model(traces):
    """Parses the model for a given trace."""
    models = {}
    for t, data in traces.items():
        for d in data:
            models.setdefault(t, []).extend(d['Intervals'])
    return models


# pylint: disable=invalid-name
def parse_trace(trace_file):
    """Parses the trace file to get a list of inactivity intervals."""
    with open(trace_file) as trace:
        trace = json.load(trace)
        trace = [i for i in trace if i['PC'] != '_Total']
        key = operator.itemgetter('PC')
        models = {}
        for pc, trace in itertools.groupby(sorted(trace, key=key), key=key):
            models[pc] = parse_model({t['Type']: t['data'] for t in trace})
        return models
