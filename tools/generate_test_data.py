#!/usr/bin/env python3
#
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

"""Generates uniform data for testing and validation."""

import argparse
import json
import sys
from simulation.static import DAYS
from simulation.static import generate_servers


def generate_data(args):
    """Generate uniform data for testing purposes."""
    data_types = {
        'inactivity': 'InactivityIntervals',
        'activity': 'ActivityIntervals',
        'off_time': 'OffIntervals',
        'off_fraction': 'OffFrequencies',
    }
    hours = [str(h).zfill(2) for h in range(24)]
    trace = []
    for server in generate_servers(args.pcs):
        for data_type, data_key in data_types.items():
            data = {}
            data['PC'] = server
            data['Type'] = data_key
            intervals = []
            for day in DAYS:
                for hour in hours:
                    if data_key != 'OffFrequencies':
                        l = [getattr(args, data_type) * args.event_count]
                    else:
                        l = [getattr(args, data_type)] * args.event_count
                    intervals.append({
                        'Day': day,
                        'Hour': hour,
                        'Intervals': l,
                    })
            data['data'] = intervals
            trace.append(data)
    return trace


def main():
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',
                        dest='output_file', default='output.json',
                        help='path for the output file')
    parser.add_argument('--pcs',
                        type=int, default=20,
                        help='number of PCs to generate')
    parser.add_argument('--inactivity',
                        type=float, default=300,
                        help='average inactivity time')
    parser.add_argument('--activity',
                        type=float, default=60,
                        help='average activity time')
    parser.add_argument('--off_time',
                        type=float, default=3600,
                        help='average off time')
    parser.add_argument('--off_fraction',
                        type=float, default=0.0,
                        help='average off fraction')
    parser.add_argument('--event_count',
                        type=int, default=10,
                        help='number of events to generate')
    args = parser.parse_args()
    with open(args.output_file, 'w') as output:
        json.dump(generate_data(args), output)


if __name__ == '__main__':
    sys.exit(main())
