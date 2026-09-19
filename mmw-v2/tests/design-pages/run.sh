#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/tests/design-pages/run.sh [-k <pattern>]
#
# unittest over a miniature handoff package; Node runs the page LOGIC, no browser.
# `node` has to be on PATH; without it the run fails rather than passing on
# half the tests.
#
# A skip count other than 0, or a run count of 0, exits non-zero and does not
# print `all passed`.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

pattern=""
if [[ $# -ne 0 ]]; then
  if [[ $# -ne 2 || "$1" != "-k" || -z "$2" ]]; then
    echo "usage: $0 [-k <pattern>]" >&2
    exit 2
  fi
  pattern="$2"
fi

if ! command -v node >/dev/null 2>&1; then
  echo "design-pages failed: node is not on PATH" >&2
  exit 1
fi

if python3 -u - "$HERE" "$pattern" <<'PY'
import sys
import unittest

here = sys.argv[1]
name_pattern = sys.argv[2]
loader = unittest.defaultTestLoader
if name_pattern:
    if "*" not in name_pattern:
        name_pattern = f"*{name_pattern}*"
    loader.testNamePatterns = [name_pattern]
suite = loader.discover(here, pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=1).run(suite)
ran = result.testsRun
skipped = len(result.skipped)
print(f"ran {ran} skipped {skipped}")
if skipped:
    print(f"refusing: skipped {skipped}", file=sys.stderr)
    sys.exit(1)
if ran < 1:
    print("refusing: ran 0", file=sys.stderr)
    sys.exit(1)
if not result.wasSuccessful():
    print("failures above", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PY
then
  echo "all passed"
else
  exit 1
fi
