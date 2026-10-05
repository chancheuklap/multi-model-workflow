#!/usr/bin/env bash
# Run the setup-mmw tests. Run after any change to the setup-mmw skill's scripts, or to the
# label table in verify-ticket.py they read.
#
#   bash mmw-v3/tests/setup-mmw/run.sh [<name pattern>]
#
# test_setup.py, unittest: labels.py creates only the labels a repository lacks and keeps the
# ones it has; space.py creates or repairs the repository's Space, and under --check reads
# only; check.py reports a set-up repository as SETUP OK and a bare one item by item,
# writing nothing either way.
#
# Needs only python3. Every gh, nmem and git command is answered by a fake inside the test,
# so nothing reaches GitHub, Nowledge Mem or a real repository.

set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
python3 "$HERE/../lib/run_unittests.py" "$HERE" "${1:-}"
echo "all passed"
