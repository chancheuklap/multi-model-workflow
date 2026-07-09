#!/usr/bin/env bash
# host.sh 宿主检测与路径/工具约定
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/host.sh
. "$SCRIPT_DIR/../lib/host.sh"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_host.sh ==="

# explicit override
MMW_HOST=claude
[ "$(mmw_host)" = "claude" ] && ok "MMW_HOST=claude" || no "MMW_HOST=claude"
[ "$(mmw_state_subdir)" = ".claude/multi-model-workflow" ] && ok "claude state path" || no "claude state path"
[ "$(mmw_worktrees_rel)" = ".claude/worktrees" ] && ok "claude worktrees path" || no "claude worktrees path"
[ "$(mmw_shell_tool)" = "Bash" ] && ok "claude shell=Bash" || no "claude shell"
[ "$(mmw_ask_user_tool)" = "AskUserQuestion" ] && ok "claude ask=AskUserQuestion" || no "claude ask"
[ "$(mmw_worker_backend)" = "codex-cli" ] && ok "claude worker=codex-cli" || no "claude worker"

MMW_HOST=droid
[ "$(mmw_host)" = "droid" ] && ok "MMW_HOST=droid" || no "MMW_HOST=droid"
[ "$(mmw_state_subdir)" = ".factory/multi-model-workflow" ] && ok "droid state path" || no "droid state path"
[ "$(mmw_worktrees_rel)" = ".factory/worktrees" ] && ok "droid worktrees path" || no "droid worktrees path"
[ "$(mmw_shell_tool)" = "Execute" ] && ok "droid shell=Execute" || no "droid shell"
[ "$(mmw_ask_user_tool)" = "AskUser" ] && ok "droid ask=AskUser" || no "droid ask"
[ "$(mmw_worker_backend)" = "droid-task" ] && ok "droid worker=droid-task" || no "droid worker"

# auto-detect via DROID_PLUGIN_ROOT when MMW_HOST unset
unset MMW_HOST
export DROID_PLUGIN_ROOT="/tmp/fake-droid-plugin"
[ "$(mmw_host)" = "droid" ] && ok "auto droid via DROID_PLUGIN_ROOT" || no "auto droid"
unset DROID_PLUGIN_ROOT
[ "$(mmw_host)" = "claude" ] && ok "default claude" || no "default claude"

# enter-worktree hint differs by host
MMW_HOST=claude
hint="$(mmw_enter_worktree_hint /tmp/wt)"
echo "$hint" | grep -q EnterWorktree && ok "claude enter hint uses EnterWorktree" || no "claude enter hint"
MMW_HOST=droid
hint="$(mmw_enter_worktree_hint /tmp/wt)"
echo "$hint" | grep -q 'cd /tmp/wt' && ok "droid enter hint uses cd" || no "droid enter hint"

# state ignore helpers
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
MMW_HOST=droid
mmw_ensure_state_ignore "$TMP"
[ -f "$TMP/.factory/.gitignore" ] && grep -qxF 'multi-model-workflow/' "$TMP/.factory/.gitignore" \
  && ok "droid ensure_state_ignore" || no "droid ensure_state_ignore"
mmw_ensure_wt_state_ignore "$TMP/wt"
[ "$(cat "$TMP/wt/.factory/.gitignore" 2>/dev/null)" = "*" ] && ok "droid wt state ignore" || no "droid wt state ignore"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
