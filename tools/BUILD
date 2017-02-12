#  -*- mode: python -*-

py_library(
    name = "parse_trace",
    srcs = ["parse_trace.py"],
    srcs_version = "PY3",
)

py_binary(
    name = "plot_histogram",
    srcs = ["plot_histogram.py"],
    data = ["//:data"],
    srcs_version = "PY3",
    deps = [
        ":parse_trace",
        "//simulation:static",
    ],
)

py_binary(
    name = "plot_satisfaction",
    srcs = ["plot_satisfaction.py"],
    data = ["//:data"],
    srcs_version = "PY3",
    deps = [
        ":parse_trace",
        "//simulation:static",
    ],
)
