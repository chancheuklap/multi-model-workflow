#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/tests/verify-ticket/run.sh [-k <pattern>]
#
# Two engines, two test runners:
#
#   this directory                    unittest, against fixed ticket bodies
#   mmw-v2/upstream-unlazy/tests      node, the vendored engine's run-tests.mjs and
#                                     lint-tests.mjs; unlazy's other suites there cover
#                                     parts this skill does not use and are not run
#
# `-k` selects unittest cases by the same substring / glob `python3 -m unittest -k`
# accepts, and skips the node suites. Without `-k` both engines run.
#
# Neither needs the tracker, a terminal or a browser. `node` has to be on PATH for
# the second one; without it the run fails rather than passing on half the tests.
#
# Under `-k`, a skip count other than 0, or a run count of 0, exits non-zero and
# does not print `all passed`.

set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_upstream_em_dashes.py" >&2 || exit 1

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
GATE_TESTS="$(dirname -- "$(dirname -- "$HERE")")/upstream-unlazy/tests"

# `verify-ticket.py` takes the ticket it is about from `MMW_TICKET` when no number is on
# the command line, and a worker session sets it. Under one, a test that means to
# exercise a made-up ticket would act on the real one that session is working. Measured
# 2026-09-10 on #320. The suite also tests judge ownership itself, so an outer acceptance
# run's ownership marker must not make those inner judges skip their release.
unset MMW_TICKET MMW_JUDGE_LEASE_OWNER
# shellcheck source-path=SCRIPTDIR
# shellcheck source=../lib/parse_k.sh
. "$HERE/../lib/parse_k.sh"  # mmw-v2/tests/lib/parse_k.sh

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

if [[ -n "$pattern" ]]; then
  if python3 -u "$HERE/../lib/run_unittests.py" "$HERE" "$pattern"; then
    echo "all passed"
    exit 0
  fi
  exit 1
fi

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
