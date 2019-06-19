#!/bin/bash

git filter-branch -f --prune-empty --tree-filter "
    find . -name '*.json' -exec ./anonnymise_trace.py {} {} \;
" --tag-name-filter cat -- --all
