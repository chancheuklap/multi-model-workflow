#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/skills/drive-target/tests/run.sh
#
# unittest over the driver, the two judges, the lease, the hook and the refusal text.
# No tracker, no terminal, no browser.
#
# Without numpy and Pillow, test_visual_parity.py's TestShrunkPixels is skipped.
# To run that class: uv run --with numpy --with pillow python -m unittest

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL="$(dirname -- "$HERE")"

# A lease registry of its own. The driver claims this machine's instance slots before it
# runs any command a repository declares, so a suite that exercises that path would
# otherwise fill the real registry with directories that stop existing when it ends.
MMW_HOME="$(mktemp -d)"
export MMW_HOME
trap 'rm -rf "$MMW_HOME"' EXIT

if python3 - "$HERE" "$SKILL" <<'PY'
import sys
import unittest

here, skill = sys.argv[1], sys.argv[2]
suite = unittest.defaultTestLoader.discover(here, pattern="test_*.py", top_level_dir=skill)
result = unittest.TextTestRunner(verbosity=1).run(suite)
print(f"skipped {len(result.skipped)}")
sys.exit(0 if result.wasSuccessful() else 1)
PY
then
  echo "all passed"
else
  echo "failures above" >&2
  exit 1
fi
