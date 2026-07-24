#!/usr/bin/env bash
# MMW worktree 初始化合同：只调用项目自有 hook，不理解项目生成物或 Graphify 元数据。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/runtime.sh
. "$SCRIPT_DIR/../lib/runtime.sh"

fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
REPO="$TMP/repo"
TARGET="$TMP/target"
mkdir -p "$REPO/.pi"
git -C "$REPO" init -q
git -C "$REPO" config user.email test@example.com
git -C "$REPO" config user.name Test
cat >"$REPO/.pi/worktree-init.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
source_wt="$1"
target_wt="$2"
printf '%s\n' "$source_wt" >"$target_wt/.pi/init-source"
printf '%s\n' "$target_wt" >"$target_wt/.pi/init-target"
SH
chmod +x "$REPO/.pi/worktree-init.sh"
printf 'seed\n' >"$REPO/seed.txt"
git -C "$REPO" add -A
git -C "$REPO" commit -qm base
git -C "$REPO" worktree add -q "$TARGET" HEAD

if mmw_prepare_worktree "$REPO" "$TARGET" >/dev/null 2>"$TMP/hook.err" \
  && [ "$(cat "$TARGET/.pi/init-source")" = "$REPO" ] \
  && [ "$(cat "$TARGET/.pi/init-target")" = "$TARGET" ]; then
  ok "project worktree hook receives source and target"
else
  no "project worktree hook invocation"
fi

cat >"$TARGET/.pi/worktree-init.sh" <<'SH'
#!/usr/bin/env bash
printf 'fixture failure\n' >&2
exit 9
SH
chmod +x "$TARGET/.pi/worktree-init.sh"
if mmw_prepare_worktree "$REPO" "$TARGET" >/dev/null 2>"$TMP/fail.err" \
  && grep -q 'WARNING' "$TMP/fail.err" \
  && grep -q 'fixture failure' "$TMP/fail.err"; then
  ok "project hook failure is visible and non-blocking"
else
  no "project hook failure contract"
fi

PLAIN="$TMP/plain"
PLAIN_TARGET="$TMP/plain-target"
mkdir -p "$PLAIN"
git -C "$PLAIN" init -q
git -C "$PLAIN" config user.email test@example.com
git -C "$PLAIN" config user.name Test
printf 'plain\n' >"$PLAIN/plain.txt"
git -C "$PLAIN" add plain.txt
git -C "$PLAIN" commit -qm plain
git -C "$PLAIN" worktree add -q "$PLAIN_TARGET" HEAD
if mmw_prepare_worktree "$PLAIN" "$PLAIN_TARGET" >/dev/null 2>"$TMP/plain.err" \
  && [ ! -s "$TMP/plain.err" ]; then
  ok "repository without worktree hook is an exact no-op"
else
  no "hook-free repository no-op"
fi

if ! grep -Eq 'agentflow_build|scripts/dev/knowledge_graph|graphify-out' "$SCRIPT_DIR/../lib/runtime.sh"; then
  ok "MMW runtime contains no project-specific graph contract"
else
  no "MMW runtime still knows a project graph schema"
fi

exit "$fail"
