#!/usr/bin/env bash
# Tests mmw-v4/install.sh. Run after a change to install.sh, prompt/render.py, or the hooks it registers.
#
#   bash mmw-v4/tests/install/run.sh
#
#   test_install.py   install.sh in a throwaway home (MMW_INSTALL_HOME) with fake orca, nmem, paseo
#                     and launchctl on PATH: the takeover of a machine mmw-v3/install.sh set up,
#                     --back, --check and its handover, the models.json rows
#
# Needs bash, python3 and uv, and mmw-v3/ beside mmw-v4/.

set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_wiring.py" || { echo "the skill set names a playbook, principle, skill, file or dispatch.sh command that is not there (above); fix it before running this suite" >&2; exit 1; }
uv run -q "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_skill_frontmatter.py" >&2 || exit 1
python3 -m unittest discover -s "$(dirname -- "${BASH_SOURCE[0]}")" -p 'test_*.py'
echo "all passed"
