#!/usr/bin/env bash
# Test reply-check.py as a process with both hosts' Stop payloads and Claude Code's Artifact
# payload, temporary repositories, glossaries and MMW_HOME, and fake runner self answers.
# Needs python3, git and uv.
set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_wiring.py" || { echo "the skill set names a playbook, principle, skill, file or dispatch.sh command that is not there (above); fix it before running this suite" >&2; exit 1; }
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_host_neutrality.py" || { echo "the skill set contains host-specific wording or a stale exception (above); fix the named line before running this suite" >&2; exit 1; }
uv run -q "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_skill_frontmatter.py" >&2 || exit 1

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

python3 "$HERE/../lib/run_unittests.py" "$HERE" ""
echo "all passed"
