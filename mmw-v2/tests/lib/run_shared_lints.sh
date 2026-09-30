#!/usr/bin/env bash
# Shared lints. Every suite's run.sh calls this once before its own tests.
# The command lines below are the list of shared lints, and the only one:
# a new shared lint is one more line here.

set -euo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
python3 "$HERE/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
python3 "$HERE/check_upstream_em_dashes.py" >&2 || exit 1
uv run "$HERE/check_own_skill_frontmatter.py" >&2 || exit 1
uv run --quiet "$HERE/check_component_structure.py" >&2 || exit 1
uv run --quiet "$HERE/check_wiring.py" >&2 || exit 1
