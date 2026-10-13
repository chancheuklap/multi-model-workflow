#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v4/tests/design-pages/run.sh [-k <pattern>]
#
# Real pull processes and headless Chromium against a local preview fake.
# Needs uv and Playwright's Chromium; never contacts Claude Design.
#
# A skip count other than 0, or a run count of 0, exits non-zero and does not
# print `all passed`.

set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_wiring.py" || { echo "the skill set names a playbook, principle, skill, file or dispatch.sh command that is not there (above); fix it before running this suite" >&2; exit 1; }
uv run -q "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_skill_frontmatter.py" >&2 || exit 1

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source-path=SCRIPTDIR
# shellcheck source=../lib/parse_k.sh
. "$HERE/../lib/parse_k.sh"  # mmw-v4/tests/lib/parse_k.sh

if uv run --quiet --with 'playwright>=1.58' python -u "$HERE/../lib/run_unittests.py" "$HERE" "$pattern"; then
  echo "all passed"
else
  exit 1
fi
