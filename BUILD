filegroup(
    name = "config",
    srcs = glob(["config/*.ini"]),
)

filegroup(
    name = "data",
    srcs = glob([
        "data/*.json",
    ]),
    visibility = ["//tools:__pkg__"],
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
        "//simulation",
        "//simulation:configuration",
    ],
)
