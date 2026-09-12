#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/tests/verify-ticket/run.sh
#
# Two engines, two test runners:
#
#   this directory                    unittest, against fixed ticket bodies
#   scripts/gate-check/tests          node, the vendored engine's own suite
#
# Neither needs the tracker, a terminal or a browser. `node` has to be on PATH for
# the second one; without it the run fails rather than passing on half the tests.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL="$(dirname -- "$(dirname -- "$HERE")")/skills/verify-ticket"
GATE_TESTS="$SKILL/scripts/gate-check/tests"

# A lease registry of its own. The driver claims this machine's instance slots before it
# runs any command a repository declares, so a suite that exercises that path would
# otherwise fill the real registry with directories that stop existing when it ends.
MMW_HOME="$(mktemp -d)"
export MMW_HOME
trap 'rm -rf "$MMW_HOME"' EXIT

# Ports of its own as well. A registry of its own isolates the registrations, not the
# ports: the default block (21000 upward) is the one every real run on this machine is
# given, so a suite left on it asks whether a live product's ports are free — and is
# told, correctly, that they are not, and a release that should succeed is refused. The
# block is probed once and not held; each run starts its search at its own offset, so two
# suites at once almost never share one.
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

# `verify-ticket.py` takes the ticket it is about from `MMW_TICKET` when no number is on
# the command line, and a worker session sets it. Under one, a test that means to
# exercise a made-up ticket would act on the real one that session is working. Measured
# 2026-09-10 on #320.
unset MMW_TICKET

rc=0

echo "### unittest"
if python3 -m unittest discover -s "$HERE" -p 'test_*.py'; then
  echo "### unittest passed"
else
  echo "### unittest failed" >&2
  rc=1
fi

echo
echo "### gate-check"
if ! command -v node >/dev/null 2>&1; then
  echo "### gate-check failed: node is not on PATH" >&2
  rc=1
elif (cd "$GATE_TESTS" && node run-tests.mjs && node lint-tests.mjs); then
  echo "### gate-check passed"
else
  echo "### gate-check failed" >&2
  rc=1
fi

echo
if [ "$rc" -eq 0 ]; then
  echo "all passed"
else
  echo "failures above" >&2
fi
exit "$rc"
