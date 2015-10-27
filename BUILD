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
)

py_library(
    name = "computer",
    srcs = ["computer.py"],
    deps = [
        ":agent",
        ":base",
        ":stats",
    ],
)

filegroup(
    name = "config",
    srcs = [
        "config.ini",
        "config_dev.ini",
    ],
)

filegroup(
    name = "data",
    srcs = glob(["data/*.csv"]),
)

py_library(
    name = "distribution",
    srcs = ["distribution.py"],
)

cc_library(
    name = "sqlitefunctions",
    srcs = ["extension-functions.c"],
    copts = ["-fno-common"],
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
    deps = [":singleton"],
    data = [":sqlitefunctions"],
)

py_library(
    name = "plot",
    srcs = ["plot.py"],
    deps = [":stats"],
)

py_library(
    name = "request",
    srcs = ["request.py"],
    deps = [
        ":base",
        ":stats",
    ],
)

py_library(
    name = "simulation",
    srcs = ["simulation.py"],
    deps = [
        ":activity_distribution",
        ":base",
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
        ":activity_distribution",
        ":base",
        ":static",
    ],
)

py_library(
    name = "user",
    srcs = ["user.py"],
    deps = [
        ":activity_distribution",
        ":base",
        ":computer",
        ":module",
        ":request",
        ":stats",
    ],
)
