#!/usr/bin/env bash
# MMW worktree 初始化合同：项目 hook 优先；普通仓库走插件内 graphify ensure。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/runtime.sh
. "$SCRIPT_DIR/../lib/runtime.sh"

fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 伪造插件根：ensure 写成可记录参数的 stub，不依赖 PATH。
FAKE_PLUGIN="$TMP/fake-plugin"
mkdir -p "$FAKE_PLUGIN/skills/graphify/scripts"
export CURSOR_PLUGIN_ROOT="$FAKE_PLUGIN"
export PI_GRAPHIFY_TEST_LOG="$TMP/graph-manager.args"
cat >"$FAKE_PLUGIN/skills/graphify/scripts/graphify_ensure.py" <<'PY'
#!/usr/bin/env python3
import os, sys
log = os.environ["PI_GRAPHIFY_TEST_LOG"]
with open(log, "w", encoding="utf-8") as f:
    f.write("\n".join(sys.argv[1:]) + "\n")
if os.environ.get("PI_GRAPHIFY_TEST_FAIL") == "1":
    print("fixture graph failure", file=sys.stderr)
    raise SystemExit(7)
print("REUSED fixture warnings=0")
PY
chmod +x "$FAKE_PLUGIN/skills/graphify/scripts/graphify_ensure.py"

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
  ok "project worktree hook wins over plugin ensure"
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
  ok "hook-free repository uses plugin ensure with space-safe paths"
else
  no "plugin ensure fallback contract"
fi

if PI_GRAPHIFY_TEST_FAIL=1 mmw_prepare_worktree "$PLAIN" "$PLAIN_TARGET" >"$TMP/generic-fail.out" 2>"$TMP/generic-fail.err" \
  && [ ! -s "$TMP/generic-fail.out" ] \
  && grep -q 'fixture graph failure' "$TMP/generic-fail.err" \
  && grep -q '通用图谱初始化失败' "$TMP/generic-fail.err"; then
  ok "plugin ensure failure is visible and non-blocking"
else
  no "plugin ensure failure contract"
fi

rm -f "$FAKE_PLUGIN/skills/graphify/scripts/graphify_ensure.py"
if mmw_prepare_worktree "$PLAIN" "$PLAIN_TARGET" >"$TMP/missing.out" 2>"$TMP/missing.err" \
  && [ ! -s "$TMP/missing.out" ] \
  && grep -q '找不到插件内 graphify ensure' "$TMP/missing.err"; then
  ok "missing plugin ensure is visible and non-blocking"
else
  no "missing plugin ensure contract"
fi

exit "$fail"
