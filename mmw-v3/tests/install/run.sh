#!/usr/bin/env bash
# Run the tests of mmw-v3/install.sh, mmw-v3/hook-launcher.py and the mmw-mode skill's
# mode-hook.py. Run after any change to one of them, to mmw-v3/skills.txt, or to what
# install.sh reads from mmw-mode/scripts/.
#
#   bash mmw-v3/tests/install/run.sh
#
#   test_install_over_v2.py          install over a home that holds an mmw-v2 install; --check
#                                    before and after; a second install; --check handed over
#   test_install_skill_list.py       skills.txt lines, links in both skill directories
#   test_install_mode_hook.py        the mode-hook registrations and Codex trust
#   test_install_guards.py           which services an isolated install calls, where it writes
#   test_install_check.py            what --check reports on its own
#   test_install_orca_folder.py      Orca worktree visibility for Git repositories only
#   test_hook_launcher.py            hook-launcher.py against a copied mmw-mode/scripts
#   test_hook_launcher_installed.py  the launcher an isolated install copies
#   test_mode_hook.py                mode-hook.py's context lines and silent failures
#
# Needs bash and python3 3.11 or later (install.sh reads TOML with tomllib). Every
# install runs against a temporary home through MMW_V3_HOME and MMW_HOME, with fake
# `orca`, `paseo`, `launchctl` and `nmem` first on a PATH that otherwise holds only the
# system directories; none needs the network, a host, a terminal or a browser.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# The suite runs its own fixtures, so the identity of the session running it comes off
# the environment first: a variable a worker session sets would otherwise reach the
# scripts under test.
unset MMW_CATALOG_MODE MMW_ROLE MMW_RUNNER MMW_HOST_CATALOG MMW_V3_HOME MMW_V3_LAUNCHCTL
unset MMW_SPEC MMW_TICKET MMW_TASK_SCOPE MMW_KIND MMW_EVENTS_PY MMW_BASE_REF
unset PASEO_AGENT_ID PASEO_AGENT_CWD ORCA_TERMINAL_HANDLE HERDR_PANE_ID HERDR_ENV TMUX
unset GROK_AGENT GROK_HOOK_EVENT CODEX_HOME PI_HOME PI_CODING_AGENT_DIR
while IFS='=' read -r name _; do
  case "$name" in NMEM_*) unset "$name" ;; esac
done < <(env)

MMW_HOME="$(mktemp -d)"
export MMW_HOME
export PYTHONDONTWRITEBYTECODE=1
trap 'rm -rf "$MMW_HOME"' EXIT

if python3 -m unittest discover -s "$HERE" -p 'test_*.py'; then
  echo "all passed"
else
  echo "failures above" >&2
  exit 1
fi
