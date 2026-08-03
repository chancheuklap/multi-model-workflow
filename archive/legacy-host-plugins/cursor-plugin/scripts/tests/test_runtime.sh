#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/runtime.sh
. "$SCRIPT_DIR/../lib/runtime.sh"

fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

[ "$(mmw_state_subdir)" = ".cursor/multi-model-workflow" ] && ok "fixed state path" || no "state path"
[ "$(mmw_worktrees_rel)" = ".cursor/worktrees" ] && ok "fixed worktree path" || no "worktree path"
[ "$(mmw_worker_branch_prefix)" = worker ] && ok "worker branch prefix" || no "branch prefix"
[ "$(mmw_shell_tool)" = Shell ] && ok "Shell tool" || no "shell tool"
[ "$(mmw_ask_user_tool)" = AskQuestion ] && ok "AskQuestion tool name" || no "ask tool"
howto="$(mmw_ask_user_howto)"
printf '%s' "$howto" | grep -q 'AskQuestion' \
  && printf '%s' "$howto" | grep -q 'cursor_dialog' \
  && printf '%s' "$howto" | grep -q '固定选项' \
  && ok "ask-user howto covers mount+fallback" || no "ask-user howto"
[ "$(mmw_worker_backend)" = cursor-task ] && ok "cursor-task backend" || no "worker backend"
[ "$(mmw_resolve_state_subdir /tmp)" = ".cursor/multi-model-workflow" ] && ok "state resolution is fixed" || no "state resolution"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git -C "$TMP" init -q
git -C "$TMP" config user.email t@t
git -C "$TMP" config user.name t
echo x >"$TMP/base.txt"
git -C "$TMP" add base.txt
git -C "$TMP" commit -qm base
mkdir -p "$TMP/.cursor/worktrees"
git -C "$TMP" worktree add -q "$TMP/.cursor/worktrees/demo" -b demo HEAD
mkdir -p "$TMP/.cursor/worktrees/demo/.cursor/multi-model-workflow"
printf '{"slug":"demo"}\n' > "$TMP/.cursor/worktrees/demo/.cursor/multi-model-workflow/task.json"

[ "$(mmw_find_worktree "$TMP" demo)" = "$TMP/.cursor/worktrees/demo" ] && ok "find worktree" || no "find worktree"
mmw_foreach_flying_manifest "$TMP" | grep -q 'task.json$' &&
  ok "list flying manifest" || no "list flying manifest"

exit "$fail"
