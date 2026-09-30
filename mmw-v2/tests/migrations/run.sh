#!/usr/bin/env bash
# Tests the one-time migrations with python3, git, a fake tracker and isolated MMW_HOME.
set -euo pipefail
bash "$(dirname -- "${BASH_SOURCE[0]}")/../lib/run_shared_lints.sh" || exit 1
cd "$(dirname "$0")"
python3 -m unittest -q test_remove_verifier.py
echo "all passed"
