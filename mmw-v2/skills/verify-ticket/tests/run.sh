#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/skills/verify-ticket/tests/run.sh
#
# Two engines, two test runners:
#
#   this directory                    unittest, against fixed ticket bodies
#   scripts/gate-check/tests          node, the vendored engine's own suite
#
# Neither needs the tracker, a terminal or a browser. `node` has to be on PATH for
# the second one; without it the run fails rather than passing on half the tests.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL="$(dirname -- "$HERE")"
GATE_TESTS="$SKILL/scripts/gate-check/tests"

# A lease registry of its own. The driver claims this machine's instance slots before it
# runs any command a repository declares, so a suite that exercises that path would
# otherwise fill the real registry with directories that stop existing when it ends.
MMW_HOME="$(mktemp -d)"
export MMW_HOME
trap 'rm -rf "$MMW_HOME"' EXIT

rc=0

echo "### unittest"
# -t is the skill directory: the test modules import each other as `tests.<name>`.
if python3 -m unittest discover -s "$HERE" -t "$SKILL" -p 'test_*.py'; then
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
