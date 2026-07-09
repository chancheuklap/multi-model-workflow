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

# invalid MMW_HOST fail-closed
MMW_HOST=foo
if mmw_host >/dev/null 2>&1; then no "invalid MMW_HOST should fail"; else ok "invalid MMW_HOST fail-closed"; fi
unset MMW_HOST

# auto-detect via DROID_PLUGIN_ROOT when MMW_HOST unset
export DROID_PLUGIN_ROOT="/tmp/fake-droid-plugin"
[ "$(mmw_host)" = "droid" ] && ok "auto droid via DROID_PLUGIN_ROOT" || no "auto droid"
unset DROID_PLUGIN_ROOT
# default claude 必须在中性路径判:若本测试从 .factory/.claude 安装目录跑,in-place 的 host.sh 会被路径自检改判
NTMP="$(mktemp -d)"; mkdir -p "$NTMP/neutral/lib"; cp "$SCRIPT_DIR/../lib/host.sh" "$NTMP/neutral/lib/host.sh"
[ "$(bash -c "unset DROID_PLUGIN_ROOT MMW_HOST; . '$NTMP/neutral/lib/host.sh'; mmw_host")" = "claude" ] \
  && ok "default claude(中性路径)" || no "default claude"
rm -rf "$NTMP"

# path self-detect:脚本装在哪个宿主插件目录下就是谁(无 env,无 MMW_HOST)
PTMP="$(mktemp -d)"
mkdir -p "$PTMP/.factory/plugins/mmw/scripts/lib" "$PTMP/.claude/plugins/mmw/scripts/lib"
cp "$SCRIPT_DIR/../lib/host.sh" "$PTMP/.factory/plugins/mmw/scripts/lib/host.sh"
cp "$SCRIPT_DIR/../lib/host.sh" "$PTMP/.claude/plugins/mmw/scripts/lib/host.sh"
[ "$(bash -c ". '$PTMP/.factory/plugins/mmw/scripts/lib/host.sh'; mmw_host")" = "droid" ] \
  && ok "path self-detect droid (.factory/plugins)" || no "path self-detect droid"
[ "$(bash -c ". '$PTMP/.claude/plugins/mmw/scripts/lib/host.sh'; mmw_host")" = "claude" ] \
  && ok "path self-detect claude (.claude/plugins)" || no "path self-detect claude"
# env 优先于路径:.claude 路径下设 DROID_PLUGIN_ROOT 仍判 droid
[ "$(bash -c "export DROID_PLUGIN_ROOT=/x; . '$PTMP/.claude/plugins/mmw/scripts/lib/host.sh'; mmw_host")" = "droid" ] \
  && ok "env DROID_PLUGIN_ROOT 覆盖路径自检" || no "env 覆盖路径自检"
# MMW_HOST 优先于路径:.factory 路径下锁 claude 仍判 claude
[ "$(bash -c "export MMW_HOST=claude; . '$PTMP/.factory/plugins/mmw/scripts/lib/host.sh'; mmw_host")" = "claude" ] \
  && ok "MMW_HOST 覆盖路径自检" || no "MMW_HOST 覆盖路径自检"
rm -rf "$PTMP"

# branch prefix helper
MMW_HOST=claude
[ "$(mmw_worker_branch_prefix)" = "codex" ] && ok "claude branch prefix codex" || no "claude branch prefix"
MMW_HOST=droid
[ "$(mmw_worker_branch_prefix)" = "worker" ] && ok "droid branch prefix worker" || no "droid branch prefix"
unset MMW_HOST

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
