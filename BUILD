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
    deps = [":module"],
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
    deps = [":simulation"],
    srcs_version = "PY3",
)

py_library(
    name = "module",
    srcs = ["module.py"],
    deps = [
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

py_library(
    name = "static",
    srcs = ["static.py"],
    srcs_version = "PY2AND3",
)

py_library(
    name = "stats",
    srcs = ["stats.py"],
    deps = [
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
        ":module",
        ":stats",
    ],
    srcs_version = "PY3",
)
