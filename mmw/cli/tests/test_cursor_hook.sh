#!/usr/bin/env bash
# Cursor postToolUse：一律退出 0；诊断在 stdout 的 additional_context。
# 不要复用 Codex hook 的退出码 2——Cursor 会把它当成挡住这次工具调用。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/../../toolchain/hooks/cursor-post-tool-use.sh"

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
FAKE="$WORK/bin"
mkdir -p "$FAKE"

run_hook() {
  set +e
  printf '%s' "$1" | env PATH="$FAKE:$PATH" bash "$HOOK" > "$WORK/out"
  echo $? > "$WORK/rc"
  set -e
}

run_hook '{}'
check "空 payload 退出 0" "0" "$(cat "$WORK/rc")"
check "空 payload 输出空对象" "{}" "$(jq -c . "$WORK/out")"

run_hook '{"tool_name":"Write","tool_input":{}}'
check "没有路径退出 0" "0" "$(cat "$WORK/rc")"
check "没有路径输出空对象" "{}" "$(jq -c . "$WORK/out")"

cat > "$FAKE/mmw" <<'EOF'
#!/bin/sh
echo "diag-line"
exit 1
EOF
chmod +x "$FAKE/mmw"

run_hook '{"tool_name":"Write","tool_input":{"path":"/tmp/x.ts"}}'
check "诊断失败仍退出 0" "0" "$(cat "$WORK/rc")"
check "诊断失败走 additional_context" "diag-line" \
  "$(jq -r .additional_context "$WORK/out")"

run_hook '{"tool_name":"StrReplace","tool_input":{"filePath":"/tmp/y.ts"}}'
check "filePath 字段同样交诊断" "diag-line" \
  "$(jq -r .additional_context "$WORK/out")"
check "filePath 字段仍退出 0" "0" "$(cat "$WORK/rc")"

cat > "$FAKE/mmw" <<'EOF'
#!/bin/sh
exit 0
EOF

run_hook '{"tool_name":"Delete","tool_input":{"file_path":"/tmp/z.ts"}}'
check "诊断通过退出 0" "0" "$(cat "$WORK/rc")"
check "诊断通过输出空对象" "{}" "$(jq -c . "$WORK/out")"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
