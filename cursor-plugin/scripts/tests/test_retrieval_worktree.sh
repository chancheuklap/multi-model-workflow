#!/usr/bin/env bash
# MMW worktree 初始化合同：项目 hook 优先；普通仓库走用户级 pi-graphify-ensure。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/runtime.sh
. "$SCRIPT_DIR/../lib/runtime.sh"

fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
BIN="$TMP/bin with space"
mkdir -p "$BIN"
export PI_GRAPHIFY_TEST_LOG="$TMP/graph-manager.args"
cat >"$BIN/pi-graphify-ensure" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$@" >"$PI_GRAPHIFY_TEST_LOG"
if [ "${PI_GRAPHIFY_TEST_FAIL:-0}" = 1 ]; then
  echo 'fixture graph failure' >&2
  exit 7
fi
echo 'REUSED fixture warnings=0'
SH
chmod +x "$BIN/pi-graphify-ensure"
export PATH="$BIN:$PATH"

REPO="$TMP/repo"
TARGET="$TMP/target"
mkdir -p "$REPO/.cursor"
git -C "$REPO" init -q
git -C "$REPO" config user.email test@example.com
git -C "$REPO" config user.name Test
cat >"$REPO/.cursor/worktree-init.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
source_wt="$1"
target_wt="$2"
printf '%s\n' "$source_wt" >"$target_wt/.cursor/init-source"
printf '%s\n' "$target_wt" >"$target_wt/.cursor/init-target"
SH
chmod +x "$REPO/.cursor/worktree-init.sh"
printf 'seed\n' >"$REPO/seed.txt"
git -C "$REPO" add -A
git -C "$REPO" commit -qm base
git -C "$REPO" worktree add -q "$TARGET" HEAD
rm -f "$PI_GRAPHIFY_TEST_LOG"

if mmw_prepare_worktree "$REPO" "$TARGET" >"$TMP/hook.out" 2>"$TMP/hook.err" \
  && [ ! -s "$TMP/hook.out" ] \
  && [ "$(cat "$TARGET/.cursor/init-source")" = "$REPO" ] \
  && [ "$(cat "$TARGET/.cursor/init-target")" = "$TARGET" ] \
  && [ ! -e "$PI_GRAPHIFY_TEST_LOG" ]; then
  ok "project worktree hook wins over generic graph manager"
else
  no "project worktree hook precedence"
fi

cat >"$TARGET/.cursor/worktree-init.sh" <<'SH'
#!/usr/bin/env bash
printf 'fixture failure\n' >&2
exit 9
SH
chmod +x "$TARGET/.cursor/worktree-init.sh"
if mmw_prepare_worktree "$REPO" "$TARGET" >"$TMP/fail.out" 2>"$TMP/fail.err" \
  && [ ! -s "$TMP/fail.out" ] \
  && grep -q 'WARNING' "$TMP/fail.err" \
  && grep -q 'fixture failure' "$TMP/fail.err"; then
  ok "project hook failure is visible and non-blocking"
else
  no "project hook failure contract"
fi

PLAIN="$TMP/plain repo"
PLAIN_TARGET="$TMP/plain target"
mkdir -p "$PLAIN"
git -C "$PLAIN" init -q
git -C "$PLAIN" config user.email test@example.com
git -C "$PLAIN" config user.name Test
printf 'plain\n' >"$PLAIN/plain.txt"
git -C "$PLAIN" add plain.txt
git -C "$PLAIN" commit -qm plain
git -C "$PLAIN" worktree add -q "$PLAIN_TARGET" HEAD
rm -f "$PI_GRAPHIFY_TEST_LOG"
EXPECTED_ARGS="$(printf '%s\n' --repo "$PLAIN_TARGET" --source "$PLAIN")"
if mmw_prepare_worktree "$PLAIN" "$PLAIN_TARGET" >"$TMP/plain.out" 2>"$TMP/plain.err" \
  && [ ! -s "$TMP/plain.out" ] \
  && [ "$(cat "$PI_GRAPHIFY_TEST_LOG")" = "$EXPECTED_ARGS" ] \
  && grep -q 'REUSED fixture' "$TMP/plain.err"; then
  ok "hook-free repository uses generic graph manager with space-safe paths"
else
  no "generic graph fallback contract"
fi

if PI_GRAPHIFY_TEST_FAIL=1 mmw_prepare_worktree "$PLAIN" "$PLAIN_TARGET" >"$TMP/generic-fail.out" 2>"$TMP/generic-fail.err" \
  && [ ! -s "$TMP/generic-fail.out" ] \
  && grep -q 'fixture graph failure' "$TMP/generic-fail.err" \
  && grep -q '通用图谱初始化失败' "$TMP/generic-fail.err"; then
  ok "generic graph failure is visible and non-blocking"
else
  no "generic graph failure contract"
fi

if PATH="/usr/bin:/bin" mmw_prepare_worktree "$PLAIN" "$PLAIN_TARGET" >"$TMP/missing.out" 2>"$TMP/missing.err" \
  && [ ! -s "$TMP/missing.out" ] \
  && grep -q '找不到 pi-graphify-ensure' "$TMP/missing.err"; then
  ok "missing graph manager is visible and non-blocking"
else
  no "missing graph manager contract"
fi

exit "$fail"
