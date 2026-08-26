#!/usr/bin/env bash
# Cursor 隔离包装：seatbelt 只挡用户级 ~/.claude 与 ~/.codex。
# 仓库合同、~/.agents/skills 和 ~/.cursor 必须仍可读。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$HERE/../lib/cursor-isolate.sh"

pass=0
fail=0
check() {
  local name="$1" want="$2" got="$3"
  if [ "$want" = "$got" ]; then
    echo "  过  $name"
    pass=$((pass + 1))
  else
    echo "  失败 $name" >&2
    echo "       想要：$want" >&2
    echo "       得到：$got" >&2
    fail=$((fail + 1))
  fi
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home"
mkdir -p "$HOME/.claude/skills" "$HOME/.codex/skills" \
  "$HOME/.cursor" "$HOME/.agents/skills" "$HOME/project/.claude"
printf 'codex\n' > "$HOME/.codex/skills/secret.md"
printf 'claude\n' > "$HOME/.claude/skills/secret.md"
printf 'agents\n' > "$HOME/.agents/skills/ok.md"
printf 'cursor\n' > "$HOME/.cursor/ok.md"
printf 'repo\n' > "$HOME/project/.claude/ok.md"

profile="$(mmw_cursor_seatbelt_profile)"
check "profile 含 version 1" "yes" \
  "$(printf '%s\n' "$profile" | grep -q '(version 1)' && echo yes || echo no)"
check "profile 挡住 ~/.claude" "yes" \
  "$(printf '%s\n' "$profile" | grep -F "$HOME/.claude" >/dev/null && echo yes || echo no)"
check "profile 挡住 ~/.codex" "yes" \
  "$(printf '%s\n' "$profile" | grep -F "$HOME/.codex" >/dev/null && echo yes || echo no)"
check "profile 不含 file-ioctl" "yes" \
  "$(printf '%s\n' "$profile" | grep -q 'file-ioctl' && echo no || echo yes)"

real_codex="$(cd "$HOME/.codex" && pwd -P)"
if [ "$real_codex" != "$HOME/.codex" ]; then
  check "profile 含 ~/.codex 的规范路径" "yes" \
    "$(printf '%s\n' "$profile" | grep -F "$real_codex" >/dev/null && echo yes || echo no)"
fi

if [ "$(uname -s)" = "Darwin" ]; then
  if sandbox-exec -p "$profile" /bin/ls "$HOME/.codex/skills" >/dev/null 2>&1; then
    check "sandbox 拒绝 ~/.codex/skills" "yes" "no"
  else
    check "sandbox 拒绝 ~/.codex/skills" "yes" "yes"
  fi
  if sandbox-exec -p "$profile" /bin/ls "$HOME/.claude/skills" >/dev/null 2>&1; then
    check "sandbox 拒绝 ~/.claude/skills" "yes" "no"
  else
    check "sandbox 拒绝 ~/.claude/skills" "yes" "yes"
  fi
  if sandbox-exec -p "$profile" /bin/ls "$HOME/.cursor" >/dev/null 2>&1; then
    check "sandbox 允许 ~/.cursor" "yes" "yes"
  else
    check "sandbox 允许 ~/.cursor" "yes" "no"
  fi
  if sandbox-exec -p "$profile" /bin/ls "$HOME/.agents/skills" >/dev/null 2>&1; then
    check "sandbox 允许 ~/.agents/skills" "yes" "yes"
  else
    check "sandbox 允许 ~/.agents/skills" "yes" "no"
  fi
  if sandbox-exec -p "$profile" /bin/ls "$HOME/project/.claude" >/dev/null 2>&1; then
    check "sandbox 允许仓库 .claude" "yes" "yes"
  else
    check "sandbox 允许仓库 .claude" "yes" "no"
  fi
else
  echo "  跳过  非 Darwin，不跑 sandbox-exec"
fi

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
