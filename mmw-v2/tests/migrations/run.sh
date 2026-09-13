#!/usr/bin/env bash
# Tests the one-time migrations with python3, git, a fake tracker and isolated MMW_HOME.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m unittest -q test_remove_verifier.py
echo "all passed"
