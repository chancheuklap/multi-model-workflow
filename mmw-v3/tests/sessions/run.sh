#!/usr/bin/env bash
# Run the tests of how one session is started: the mmw-mode skill's models.py and its
# `dispatch.sh research <n>`. Run after any change under mmw-v3/skills/mmw-mode/scripts/.
#
#   bash mmw-v3/tests/sessions/run.sh
#
# Two engines:
#
#   test_*.py         unittest: models.json reading, defaults, validation and writing;
#                     catalog match and host argv; runner choice; roles and locations
#   test_research.sh  dispatch.sh research against a fake `paseo`, `orca`, `herdr` and
#                     `gh` on PATH
#
# Needs bash, python3 and git. None needs the tracker, the network, a terminal or a
# browser. MMW_HOME points at a temporary directory for the whole run, so nothing reads
# or writes the machine's ~/.mmw.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# The suite runs its own fixtures, so the identity of the session running it comes off
# the environment first: a variable a worker session sets would otherwise reach the
# scripts under test.
unset MMW_CATALOG_MODE MMW_ROLE MMW_RUNNER MMW_HOST_CATALOG
unset MMW_SPEC MMW_TICKET MMW_TASK_SCOPE MMW_KIND MMW_EVENTS_PY
unset PASEO_AGENT_ID ORCA_TERMINAL_HANDLE HERDR_PANE_ID HERDR_ENV TMUX
while IFS='=' read -r name _; do
  case "$name" in NMEM_*) unset "$name" ;; esac
done < <(env)

MMW_HOME="$(mktemp -d)"
export MMW_HOME
trap 'rm -rf "$MMW_HOME"' EXIT

rc=0

echo "### unittest"
if python3 -m unittest discover -s "$HERE" -p 'test_*.py'; then
  echo "### unittest passed"
else
  echo "### unittest failed" >&2
  rc=1
fi

echo
echo "### dispatch.sh research"
# dispatch.sh asks git about the current checkout, so this runs with the tests directory
# as its working directory rather than wherever run.sh was called from.
if (cd "$HERE" && bash ./test_research.sh all); then
  echo "### dispatch.sh research passed"
else
  echo "### dispatch.sh research failed" >&2
  rc=1
fi

echo
if [ "$rc" -eq 0 ]; then
  echo "all passed"
else
  echo "failures above" >&2
fi
exit "$rc"
