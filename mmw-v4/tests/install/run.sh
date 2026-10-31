#!/usr/bin/env bash
# Tests mmw-v4/install.sh. Run after a change to install.sh, prompt/, or the hooks it registers.
#
#   bash mmw-v4/tests/install/run.sh
#
#   test_install.py   install.sh in a throwaway home (MMW_INSTALL_HOME) with fake orca, gh, node, nmem,
#                     paseo, herdr and launchctl on PATH and a fake Paseo app: the takeover of a machine mmw-v3/install.sh set up,
#                     --back, --check and its handover, the models.json rows, Orca's worktree-base-path,
#                     the shared prompt links and migration, optional Paseo isolation, and base tools
#
# Needs bash, python3 and uv. Rollback uses a synthetic v3 installer.

set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_wiring.py" || { echo "the skill set names a playbook, principle, skill, file or dispatch.sh command that is not there (above); fix it before running this suite" >&2; exit 1; }
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_host_neutrality.py" || { echo "the skill set contains host-specific wording or a stale exception (above); fix the named line before running this suite" >&2; exit 1; }
uv run -q "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_skill_frontmatter.py" >&2 || exit 1
python3 -m unittest discover -s "$(dirname -- "${BASH_SOURCE[0]}")" -p 'test_*.py'
echo "all passed"
