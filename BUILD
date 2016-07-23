# -*- mode: python -*-

py_library(
    name = "activity_distribution",
    srcs = ["activity_distribution.py"],
    srcs_version = "PY3",
    deps = [
        ":base",
        ":distribution",
        ":hashable",
        ":static",
    ],
)

py_library(
    name = "base",
    srcs = ["base.py"],
    srcs_version = "PY3",
    deps = [
        ":configuration",
        ":module",
    ],
)

py_binary(
    name = "benchmark",
    srcs = ["tests/benchmark.py"],
    default_python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":distribution",
    ],
)

py_library(
    name = "computer",
    srcs = ["computer.py"],
    srcs_version = "PY3",
    deps = [
        ":activity_distribution",
        ":base",
        ":stats",
    ],
)

py_library(
    name = "configuration",
    srcs = ["configuration.py"],
    srcs_version = "PY3",
)

filegroup(
    name = "config",
    srcs = glob(["config/*.ini"]),
)

filegroup(
    name = "data",
    srcs = glob([
        "data/*.json",
    ]),
)

py_library(
    name = "distribution",
    srcs = ["distribution.py"],
    srcs_version = "PY3",
    deps = [":hashable"],
)

py_library(
    name = "hashable",
    srcs = ["hashable.py"],
    srcs_version = "PY2AND3",
)

py_library(
    name = "histogram",
    srcs = ["histogram.py"],
    srcs_version = "PY3",
    deps = [
        ":base",
        ":static",
    ],
)

py_binary(
    name = "main",
    srcs = ["main.py"],
    data = [
        ":config",
        ":data",
    ],
    default_python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":configuration",
        ":simulation",
    ],
)

py_library(
    name = "module",
    srcs = ["module.py"],
    srcs_version = "PY3",
    deps = [
        ":configuration",
        ":singleton",
        ":static",
    ],
)

py_library(
    name = "plot",
    srcs = ["plot.py"],
    srcs_version = "PY3",
    deps = [
        ":activity_distribution",
        ":static",
        ":stats",
    ],
)

py_library(
    name = "simulation",
    srcs = ["simulation.py"],
    srcs_version = "PY3",
    deps = [
        ":activity_distribution",
        ":base",
        ":configuration",
        ":histogram",
        ":module",
        ":plot",
        ":static",
        ":stats",
        ":user",
    ],
)

py_library(
    name = "singleton",
    srcs = ["singleton.py"],
    srcs_version = "PY3",
)

py_library(
    name = "static",
    srcs = ["static.py"],
    srcs_version = "PY3",
    deps = [":configuration"],
)

py_library(
    name = "stats",
    srcs = ["stats.py"],
    srcs_version = "PY3",
    deps = [
        ":activity_distribution",
        ":base",
        ":histogram",
        ":module",
        ":static",
    ],
)

py_library(
    name = "user",
    srcs = ["user.py"],
    srcs_version = "PY3",
    deps = [
        ":activity_distribution",
        ":base",
        ":computer",
        ":stats",
    ],
)
