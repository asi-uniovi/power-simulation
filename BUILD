py_library(
    name = "activity_distribution",
    srcs = ["activity_distribution.py"],
    deps = [
        ":base",
        ":static",
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
        ":base",
        ":stats",
    ],
)

filegroup(
    name = "config",
    srcs = ["config.ini"],
)

filegroup(
    name = "data",
    srcs = glob(["data/*.csv"]),
)

py_binary(
    name = "main",
    srcs = ["main.py"],
    deps = [":simulation"],
    data = [
        ":config",
        ":data",
    ],
)

py_library(
    name = "module",
    srcs = ["module.py"],
    deps = [":singleton"],
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
