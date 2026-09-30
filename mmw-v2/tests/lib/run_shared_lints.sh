#!/usr/bin/env bash
# Shared lints. Every suite's run.sh calls this once before its own tests.
# A new shared lint is one more line in this file.
#
# Today:
#   check_module_paths.py
#   check_upstream_em_dashes.py
#   check_own_skill_frontmatter.py  (through uv run; its PEP 723 block brings PyYAML)

set -euo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
python3 "$HERE/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
python3 "$HERE/check_upstream_em_dashes.py" >&2 || exit 1
uv run "$HERE/check_own_skill_frontmatter.py" >&2 || exit 1
