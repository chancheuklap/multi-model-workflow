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
# MMW_FORCE_SKIP=1: this runner skips one test. A skip count other than 0, or a
# run count of 0, exits non-zero and does not print `all passed`.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# No parent to tell. `hook.py` and the lease read `PASEO_AGENT_ID` to address the session
# that started a run; these tests exercise those paths against made-up agents, so under a
# Paseo session they would reach a live agent as news about work nobody is doing.
unset PASEO_AGENT_ID

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not on PATH" >&2
  exit 1
fi

# A lease registry of its own. The driver claims this machine's instance slots before it
# runs any command a repository declares, so a suite that exercises that path would
# otherwise fill the real registry with directories that stop existing when it ends.
MMW_HOME="$(mktemp -d)"
export MMW_HOME
trap 'rm -rf "$MMW_HOME"' EXIT

# Ports of its own as well. A registry of its own isolates the registrations, not the
# ports: the default block (21000 upward) is the one every real run on this machine is
# given, so a suite left on it asks whether a live product's ports are free — and is
# told, correctly, that they are not. The block is probed once and not held; each run
# starts its search at its own offset, so two suites at once almost never share one.
# `test_lease.py` and `test_story_parity.py` name their own base and are unaffected.
MMW_LEASE_PORT_BASE="$(python3 -c '
import os, random, socket
stride = int(os.environ.get("MMW_LEASE_PORT_STRIDE", "20"))
slots = int(os.environ.get("MMW_LEASE_SLOTS", "8"))
need = stride * slots
start = 23000 + random.randrange(0, (44000 - 23000) // need) * need
for base in list(range(start, 46000 - need, need)) + list(range(23000, start, need)):
    held = []
    try:
        for port in range(base, base + need):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("0.0.0.0", port))
            held.append(sock)
        print(base)
        break
    except OSError:
        continue
    finally:
        for sock in held:
            sock.close()
else:
    raise SystemExit("no free block of ports for this suite")
')"
export MMW_LEASE_PORT_BASE

if uv run --quiet --with numpy --with pillow python -u - "$HERE" <<'PY'
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
ran = result.testsRun
skipped = len(result.skipped)
print(f"ran {ran} skipped {skipped}")
if skipped:
    print(f"refusing: skipped {skipped}", file=sys.stderr)
    sys.exit(1)
if ran < 1:
    print("refusing: ran 0", file=sys.stderr)
    sys.exit(1)
if not result.wasSuccessful():
    print("failures above", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PY
then
  echo "all passed"
else
  exit 1
fi

