#!/usr/bin/env bash
# Checks on the text of the skills, and on the shared-lint entry every suite runs first.
#
#   bash mmw-v2/tests/skill-text/run.sh [-k <pattern>]
#
# unittest. Needs uv, which supplies pyyaml.
#
# A skip count other than 0, or a run count of 0, exits non-zero and does not
# print `all passed`.

set -euo pipefail
bash "$(dirname -- "${BASH_SOURCE[0]}")/../lib/run_shared_lints.sh" || exit 1

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# A suite run from inside a worker session must not inherit that session's ticket
# or Memory boundary (mmw-v2/tests/AGENTS.md ## Key Conventions). This suite also
# strips MMW_BASE_REF, which the verbatim check reads.
unset MMW_TICKET MMW_BASE_REF MMW_CATALOG_MODE MMW_SPEC MMW_TASK_SCOPE MMW_KIND MMW_EVENTS_PY
unset PASEO_AGENT_ID ORCA_TERMINAL_HANDLE HERDR_PANE_ID
while IFS='=' read -r name _; do
  case "$name" in NMEM_*) unset "$name" ;; esac
done < <(env)
# shellcheck source-path=SCRIPTDIR
# shellcheck source=../lib/parse_k.sh
. "$HERE/../lib/parse_k.sh"  # mmw-v2/tests/lib/parse_k.sh

if uv run --quiet --with pyyaml python -u "$HERE/../lib/run_unittests.py" "$HERE" "$pattern"; then
  echo "all passed"
else
  exit 1
fi
