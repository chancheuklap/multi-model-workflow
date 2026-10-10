#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v4/tests/verify-ticket/run.sh [-k <pattern>]
#
# Two engines, two test runners:
#
#   this directory                    unittest, against fixed ticket bodies
#   gate-check/                       node, unlazy's run-tests.mjs and lint-tests.mjs
#                                     against the engine under scripts/gate-check/
#
# `-k` selects unittest cases by the same substring / glob `python3 -m unittest -k`
# accepts, and skips the node suites. Without `-k` both engines run.
#
# Neither needs the tracker or a terminal. `node` has to be on PATH for
# the second one; without it the run fails rather than passing on half the tests.
#
# Under `-k`, a skip count other than 0, or a run count of 0, exits non-zero and
# does not print `all passed`.

set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_wiring.py" || { echo "the skill set names a playbook, principle, skill, file or dispatch.sh command that is not there (above); fix it before running this suite" >&2; exit 1; }
uv run -q "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_skill_frontmatter.py" >&2 || exit 1

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
GATE_TESTS="$HERE/gate-check"

# `verify-ticket.py` takes the ticket it is about from `MMW_TICKET` when no number is on
# the command line, and a worker session sets it. Under one, a test that means to
# exercise a made-up ticket would act on the real one that session is working. Measured
# 2026-09-10 on #320.
unset MMW_TICKET
# shellcheck source-path=SCRIPTDIR
# shellcheck source=../lib/parse_k.sh
. "$HERE/../lib/parse_k.sh"  # mmw-v4/tests/lib/parse_k.sh

if [[ -n "$pattern" ]]; then
  if python3 -u "$HERE/../lib/run_unittests.py" "$HERE" "$pattern"; then
    echo "all passed"
    exit 0
  fi
  exit 1
fi

rc=0

echo "### unittest"
if python3 -m unittest discover -s "$HERE" -p 'test_*.py'; then
  echo "### unittest passed"
else
  echo "### unittest failed" >&2
  rc=1
fi

echo
echo "### gate-check"
if ! command -v node >/dev/null 2>&1; then
  echo "### gate-check failed: node is not on PATH" >&2
  rc=1
elif (cd "$GATE_TESTS" && node run-tests.mjs && node lint-tests.mjs); then
  echo "### gate-check passed"
else
  echo "### gate-check failed" >&2
  rc=1
fi

echo
if [ "$rc" -eq 0 ]; then
  echo "all passed"
else
  echo "failures above" >&2
fi
exit "$rc"
