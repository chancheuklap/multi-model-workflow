#!/usr/bin/env bash
# Tests the pstack importer, mode scripts and ticket state against disposable fixtures.
# Usage: bash mmw-v2/tests/mmw/run.sh [-k <pattern>]
# Needs uv (supplies pyyaml), python3, node and git. Empty or skipped selections fail.

set -euo pipefail
bash "$(dirname -- "${BASH_SOURCE[0]}")/../lib/run_shared_lints.sh" || exit 1
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
unset MMW_JUDGE_LEASE_OWNER MMW_TICKET MMW_BASE_REF MMW_CATALOG_MODE MMW_SPEC MMW_TASK_SCOPE MMW_KIND MMW_EVENTS_PY MMW_ROLE
unset PASEO_AGENT_ID ORCA_TERMINAL_HANDLE HERDR_PANE_ID
while IFS='=' read -r name _; do
  case "$name" in NMEM_*) unset "$name" ;; esac
done < <(env)
# shellcheck source-path=SCRIPTDIR
# shellcheck source=../lib/parse_k.sh
. "$HERE/../lib/parse_k.sh"
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

if uv run --quiet --with pyyaml python -u "$HERE/../lib/run_unittests.py" "$HERE" "$pattern"; then
  echo "all passed"
else
  exit 1
fi
