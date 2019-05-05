# Power management simulaton for computer fleets

[![Build Status](https://travis-ci.org/asi-uniovi/power-simulation.svg?branch=master)](https://travis-ci.org/asi-uniovi/power-simulation)

## How to run this

### Pre-requisites

Install the Python dependencies:

`$ make init`

### Run the simulation

`$ pipenv run ./main.py --config=config/2015.ini`

See `pipenv run ./main.py --help` for details of the flags and options.

## References

1. [SimPy documentation](
    https://simpy.readthedocs.org)
1. [Injector's documentation](
    https://injector.readthedocs.org)
1. [Power-law Distributions in Empirical Data](
    http://tuvalu.santafe.edu/~aaronc/powerlaws/)
1. [Histograms and Kernel Density Estimation (KDE)](
    http://www.mglerner.com/blog/?p=28)
1. [Random Values from an Empirical Distribution](
    http://www.astroml.org/book_figures/chapter3/fig_clone_distribution.html)
1. [DB-API 2.0 interface for SQLite databases](
    https://docs.python.org/3/library/sqlite3.html)
1. [Building and installing NumPy](
    http://docs.scipy.org/doc/numpy/user/install.html)
1. [Mardown: Syntax](
    https://daringfireball.net/projects/markdown/syntax)
1. [SQLite PRAGMA Statements](
    https://www.sqlite.org/pragma.html)
1. [The Python Profilers](
    https://docs.python.org/3/library/profile.html)
1. [Python Performance Tips](
    https://wiki.python.org/moin/PythonSpeed/PerformanceTips)

**This is not an official Google product**.
