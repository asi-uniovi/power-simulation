#!/bin/sh

bazel query 'deps(//:main)' --output graph | dot -Tpng > bazel.png
