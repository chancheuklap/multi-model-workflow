#!/usr/bin/env bash
# Tests the checks every suite runs first. Run after a change under mmw-v4/tests/lib/.
#
#   bash mmw-v4/tests/lib/run.sh
#
#   test_check_wiring.py   check_wiring.py on a copy of mmw-v4/skills/ broken one way per case
#
# Needs only python3.

set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_host_neutrality.py" || { echo "the skill set contains host-specific wording or a stale exception (above); fix the named line before running this suite" >&2; exit 1; }
python3 -m unittest discover -s "$(dirname -- "${BASH_SOURCE[0]}")" -p 'test_*.py'
echo "all passed"
