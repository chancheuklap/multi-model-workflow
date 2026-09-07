#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/tests/drive-target/run.sh
#
# unittest over the driver, the story judge, the lease, the hook and the refusal text.
# No tracker, no terminal. The story fixture starts Chromium.
#
# Pixel classes need numpy and Pillow. The runner is
# `uv run --with numpy --with pillow`; without uv on PATH the run fails rather than
# passing on a half suite.
#
# MMW_FORCE_SKIP=1: this runner skips one test. A skip count other than 0 exits
# non-zero and does not print `all passed`.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

if ! command -v uv >/dev/null 2>&1; then
  echo "### unittest failed: uv is not on PATH" >&2
  exit 1
fi

# A lease registry of its own. The driver claims this machine's instance slots before it
# runs any command a repository declares, so a suite that exercises that path would
# otherwise fill the real registry with directories that stop existing when it ends.
MMW_HOME="$(mktemp -d)"
export MMW_HOME
trap 'rm -rf "$MMW_HOME"' EXIT

if uv run --quiet --with numpy --with pillow python - "$HERE" <<'PY'
import os
import sys
import unittest

here = sys.argv[1]
suite = unittest.defaultTestLoader.discover(here, pattern="test_*.py")
if os.environ.get("MMW_FORCE_SKIP") == "1":
    class _ForceSkip(unittest.TestCase):
        def test_mmw_force_skip(self):
            self.skipTest("MMW_FORCE_SKIP=1")
    suite.addTest(_ForceSkip("test_mmw_force_skip"))
result = unittest.TextTestRunner(verbosity=1).run(suite)
print(f"skipped {len(result.skipped)}")
if result.skipped:
    sys.exit(1)
sys.exit(0 if result.wasSuccessful() else 1)
PY
then
  echo "all passed"
else
  echo "failures above" >&2
  exit 1
fi
