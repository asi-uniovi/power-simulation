py_library(
    name = "activity_distribution",
    srcs = ["activity_distribution.py"],
    deps = [
        ":base",
        ":distribution",
        ":static",
    ],
    srcs_version = "PY3",
)

py_library(
    name = "base",
    srcs = ["base.py"],
    deps = [
        ":configuration",
        ":module",
    ],
    srcs_version = "PY3",
)

py_library(
    name = "computer",
    srcs = ["computer.py"],
    deps = [
        ":activity_distribution",
        ":base",
        ":stats",
    ],
    srcs_version = "PY3",
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
)

py_library(
    name = "histogram",
    srcs = ["histogram.py"],
    deps = [
        ":base",
        ":static",
    ],
    srcs_version = "PY3",
)

py_binary(
    name = "main",
    srcs = ["main.py"],
    data = [
        ":config",
        ":data",
    ],
    default_python_version = "PY3",
    deps = [
        ":configuration",
        ":simulation",
    ],
    srcs_version = "PY3",
)

py_library(
    name = "module",
    srcs = ["module.py"],
    data = [":sqlitefunctions"],
    deps = [
        ":configuration",
        ":singleton",
        ":static",
    ],
    srcs_version = "PY3",
)

py_library(
    name = "plot",
    srcs = ["plot.py"],
    deps = [
        ":activity_distribution",
        ":static",
        ":stats",
    ],
    srcs_version = "PY3",
)

py_library(
    name = "simulation",
    srcs = ["simulation.py"],
    deps = [
        ":activity_distribution",
        ":base",
        ":histogram",
        ":module",
        ":plot",
        ":static",
        ":stats",
        ":user",
    ],
    srcs_version = "PY3",
)

py_library(
    name = "singleton",
    srcs = ["singleton.py"],
    srcs_version = "PY3",
)

cc_library(
    name = "sqlitefunctions",
    srcs = ["extension-functions.c"],
    copts = ["-fno-common"],
)

py_library(
    name = "static",
    srcs = ["static.py"],
    deps = [":configuration"],
    srcs_version = "PY3",
)

py_library(
    name = "stats",
    srcs = ["stats.py"],
    deps = [
        ":activity_distribution",
        ":base",
        ":histogram",
        ":module",
        ":static",
    ],
    srcs_version = "PY3",
)

py_library(
    name = "user",
    srcs = ["user.py"],
    deps = [
        ":activity_distribution",
        ":base",
        ":computer",
        ":stats",
    ],
    srcs_version = "PY3",
)
