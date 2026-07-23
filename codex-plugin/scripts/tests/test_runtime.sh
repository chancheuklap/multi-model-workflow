#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/runtime.sh
. "$SCRIPT_DIR/../lib/runtime.sh"

fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

[ "$(mmw_state_subdir)" = ".codex/multi-model-workflow" ] && ok "fixed state path" || no "state path"
[ "$(mmw_worktrees_rel)" = ".codex/worktrees" ] && ok "fixed worktree path" || no "worktree path"
[ "$(mmw_worker_branch_prefix)" = worker ] && ok "worker branch prefix" || no "branch prefix"
[ "$(mmw_shell_tool)" = exec_command ] && ok "Codex shell tool" || no "shell tool"
[ "$(mmw_ask_user_tool)" = request_user_input ] && ok "Codex ask-user tool" || no "ask tool"
[ "$(mmw_worker_backend)" = codex-native-subagents ] && ok "Codex native subagent backend" || no "worker backend"
[ "$(mmw_resolve_state_subdir /tmp)" = ".codex/multi-model-workflow" ] && ok "state resolution is fixed" || no "state resolution"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/.codex/worktrees/demo/.codex/multi-model-workflow"
printf '{}\n' > "$TMP/.codex/worktrees/demo/.codex/multi-model-workflow/task.json"
mkdir -p "$TMP/.pi/worktrees/foreign/.pi/multi-model-workflow"
printf '{}\n' > "$TMP/.pi/worktrees/foreign/.pi/multi-model-workflow/task.json"
[ "$(mmw_find_worktree "$TMP" demo)" = "$TMP/.codex/worktrees/demo" ] && ok "find worktree" || no "find worktree"
mmw_foreach_flying_manifest "$TMP" | grep -q '/demo/.codex/multi-model-workflow/task.json$' &&
  ok "list flying manifest" || no "list flying manifest"
if mmw_foreach_flying_manifest "$TMP" | grep -q '/.pi/'; then
  no "Codex runtime read foreign mirror state"
else
  ok "ignore foreign mirror state"
fi

exit "$fail"
