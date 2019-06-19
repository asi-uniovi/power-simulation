#!/usr/bin/env python3

"""Replaces the name of the workstations with some that is anonymous."""

import argparse
import functools
import json
import math
import re
import sys

NAME_TEMPL = 'WORKSTATION%s.company1.net'
NAME_PATTERN = re.compile(r'^WORKSTATION\d+\.company1\.net$')


def names_generator(trace):
    """Generates a new PC name."""
    size = len(set(i['PC'] for i in trace if i['PC'] != '_Total'))
    fill = math.ceil(math.log(size, 10))
    return iter(NAME_TEMPL % str(i).zfill(fill) for i in range(size))


def print_substitutions(pcs):
    """Show a report of substitutions done."""
    for sub in pcs.items():
        print('%s -> %s' % sub)
    # print('Made %d changes.' % len(pcs))


@functools.lru_cache(maxsize=None)
def should_substitute(pc_name):
    """Indicates if a PC name should be substituted."""
    return pc_name != '_Total' and not NAME_PATTERN.match(pc_name)


def anonymise(trace):
    """Read the trace, change the workstation names and write."""
    names = names_generator(trace)
    pcs = {}
    for entry in trace:
        if should_substitute(entry['PC']):
            if entry['PC'] not in pcs:
                pcs[entry['PC']] = next(names)
            entry['PC'] = pcs[entry['PC']]
    print_substitutions(pcs)
    return trace


def main():
    """Parse arguments and run the anonymisation."""
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', type=str)
    parser.add_argument('output_file', type=str)
    args = parser.parse_args()
    with open(args.input_file, 'r') as input_file:
        trace = json.load(input_file)
    try:
        trace = anonymise(trace)
    except ValueError:
        print('Changes not done!')
    with open(args.output_file, 'w') as output_file:
        json.dump(trace, output_file)


if __name__ == '__main__':
    sys.exit(main())
