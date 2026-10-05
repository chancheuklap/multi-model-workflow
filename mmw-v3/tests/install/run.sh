#!/usr/bin/env bash
# Tests mmw-v3/install.sh: each scenario installs into a throwaway home (MMW_INSTALL_HOME)
# with fake orca, nmem, paseo, gh and launchctl on PATH, and checks what landed there.
# Run after any change to install.sh, prompt/render.py, or the hooks it registers.
#
#   bash mmw-v3/tests/install/run.sh
#
# The scenarios live in the dispatch suite's test_dispatch.sh, which owns the fakes; this
# suite runs its INSTALL list. Needs bash, python3 and uv.

set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
uv run -q "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_skill_frontmatter.py" >&2 || exit 1

DISPATCH_TESTS="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../dispatch" && pwd -P)"
unset MMW_SPEC MMW_TICKET MMW_TASK_SCOPE MMW_KIND MMW_EVENTS_PY
unset PASEO_AGENT_ID ORCA_TERMINAL_HANDLE HERDR_PANE_ID
while IFS='=' read -r name _; do
  case "$name" in NMEM_*) unset "$name" ;; esac
done < <(env)

if (cd "$DISPATCH_TESTS" && bash ./test_dispatch.sh install); then
  echo "all passed"
else
  echo "failures above" >&2
  exit 1
fi
