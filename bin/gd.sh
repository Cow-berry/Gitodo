#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
uv run --directory "$SCRIPT_DIR/../src" main.py "$@"
