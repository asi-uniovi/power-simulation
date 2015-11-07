# Power managemnet simulaton for computer fleets

## How to run this

### Using Python, pip and virtualenv

(optional) Create a Python virtualenv by using virtualenv activate it:

`$ virtualenv ~/.virtualenvs/simulacion`

`$ source ~/.virtualenvs/simulacion/bin/activate`

After cloning the repository, install the packages needed with pip:

`$ pip install -Ur requirements.txt`

You might need to install dependencies, in order to build from source the
packages, for instance, in the case of Debian/Ubuntu:

`$ sudo apt-get install python-dev libatlas-base-dev gfortran libsqlite3-dev`

Compile the SQLite extension module:

`$ gcc -fPIC -lm -shared extension-functions.c -o libsqlitefunctions.so`

`$ gcc -fno-common -dynamiclib extension-functions.c -o libsqlitefunctions.dylib`

Run the simulation with a config file:

`$ python main.py --config config.ini`

### (Experimental) Using Bazel

You can as well use [Bazel](http://bazel.io) for reproducible builds and faster
clean ups. After [installing it](), run with:

`$ bazel run -c opt :main -- --config config.ini`

Results will be found on the `bazel-out` directory.

## References

1. [SimPy documentation](
    https://simpy.readthedocs.org/en/stable/)
1. [Injector's documentation](
    https://injector.readthedocs.org/en/stable/)
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
1. [Installing Bazel](
    http://bazel.io/docs/install.html)
1. [Bazel BUILD Encyclopedia of Functions](
    http://bazel.io/docs/be/overview.html)
1. [Mardown: Syntax](
    https://daringfireball.net/projects/markdown/syntax)
1. [SQLite PRAGMA Statements](
    https://www.sqlite.org/pragma.html)
1. [The Python Profilers](
    https://docs.python.org/3/library/profile.html)
1. [Python Performance Tips](
    https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
