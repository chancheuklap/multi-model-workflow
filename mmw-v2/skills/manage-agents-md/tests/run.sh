#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/skills/manage-agents-md/tests/run.sh

set -uo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
rc=0
ENGINE_FAULTS=': unbound variable|: integer expression expected|: command not found|syntax error near'

run() {
  local label="$1"; shift
  echo; echo "### $label"
  local out ok=0
  out="$(mktemp)"
  "$@" >"$out" 2>&1 || ok=1
  cat "$out"
  if [ "$ok" -eq 0 ]; then
    if grep -qE "$ENGINE_FAULTS" "$out"; then
      echo "### $label failed: bash runtime error in output" >&2; rc=1
    else
      echo "### $label passed"
    fi
  else
    echo "### $label failed" >&2; rc=1
  fi
  rm -f "$out"
}

run "check.sh" bash "$HERE/test_check.sh"

echo
[ "$rc" -eq 0 ] && echo "all passed" || echo "failures above" >&2
exit "$rc"
