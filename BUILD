py_library(
    name = "activity_distribution",
    srcs = ["activity_distribution.py"],
    deps = [
        ":base",
        ":distribution",
        ":static",
    ],
)

py_library(
    name = "agent",
    srcs = ["agent.py"],
    deps = [
        ":activity_distribution",
        ":base",
    ],
)

py_library(
    name = "base",
    srcs = ["base.py"],
    deps = [":module"],
)

py_library(
    name = "computer",
    srcs = ["computer.py"],
    deps = [
        ":activity_distribution",
        ":base",
        ":stats",
    ],
)

filegroup(
    name = "config",
    srcs = glob(["config/*.ini"]),
)

filegroup(
    name = "data",
    srcs = glob(["data/*.csv"]),
)

py_library(
    name = "distribution",
    srcs = ["distribution.py"],
)

py_library(
    name = "histogram",
    srcs = ["histogram.py"],
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
    deps = [":simulation"],
)

py_library(
    name = "module",
    srcs = ["module.py"],
    deps = [
        ":singleton",
        ":static",
    ],
)

py_library(
    name = "plot",
    srcs = ["plot.py"],
    deps = [
        ":activity_distribution",
        ":static",
        ":stats",
    ],
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
)

py_library(
    name = "singleton",
    srcs = ["singleton.py"],
)

py_library(
    name = "static",
    srcs = ["static.py"],
)

py_library(
    name = "stats",
    srcs = ["stats.py"],
    deps = [
        ":base",
        ":histogram",
        ":module",
    ],
)

py_library(
    name = "user",
    srcs = ["user.py"],
    deps = [
        ":activity_distribution",
        ":agent",
        ":base",
        ":computer",
        ":module",
        ":stats",
    ],
)
