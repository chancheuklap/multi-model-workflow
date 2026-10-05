#!/usr/bin/env bash
# Tests the checks every suite runs first. Run after a change under mmw-v3/tests/lib/.
#
#   bash mmw-v3/tests/lib/run.sh
#
#   test_check_wiring.py   check_wiring.py on a copy of mmw-v3/skills/ broken one way per case
#
# Needs only python3.

set -euo pipefail
python3 -m unittest discover -s "$(dirname -- "${BASH_SOURCE[0]}")" -p 'test_*.py'
echo "all passed"
