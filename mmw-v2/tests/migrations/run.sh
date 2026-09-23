#!/usr/bin/env bash
# Tests the one-time migrations with python3, git, a fake tracker and isolated MMW_HOME.
set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_upstream_em_dashes.py" >&2 || exit 1
cd "$(dirname "$0")"
python3 -m unittest -q test_remove_verifier.py
echo "all passed"
