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

"""Main runner of the simulation."""

import sys
import flamegraph
import matplotlib
matplotlib.use('Agg')
import numpy
numpy.seterr('raise')
from simulation.simulation import runner


def main():
    """Just starts the simulation."""
    runner()


if __name__ == '__main__':
    flamegraph.start_profile_thread(fd=open("./perf.log", "w"))
    sys.exit(main())
