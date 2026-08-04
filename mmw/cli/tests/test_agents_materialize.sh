#!/usr/bin/env bash
# 原生 subagent 物化：型号来自 .mmw.json，frontmatter 按宿主 profile 写出。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MMW="$HERE/../mmw"
ROOT="$(cd "$HERE/../../.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

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

fm() {
  # fm <file> <key>
  sed -n "s/^$2: //p" "$1" | head -1
}

printf 'Pi 物化\n'
pi_out="$WORK/pi-agents"
mkdir -p "$pi_out"
"$MMW" agents materialize --host pi --out "$pi_out"

check "Pi 写出 planner" "yes" "$([ -f "$pi_out/mmw-planner.md" ] && echo yes || echo no)"
check "Pi 写出 worker-high-risk" "yes" "$([ -f "$pi_out/mmw-worker-high-risk.md" ] && echo yes || echo no)"
check "Pi 写出 reviewer-gpt" "yes" "$([ -f "$pi_out/mmw-reviewer-gpt.md" ] && echo yes || echo no)"
check "Pi 写出 reviewer-claude" "yes" "$([ -f "$pi_out/mmw-reviewer-claude.md" ] && echo yes || echo no)"
check "Pi 不再留单份 mmw-reviewer" "no" "$([ -f "$pi_out/mmw-reviewer.md" ] && echo yes || echo no)"

check "Pi planner 型号" "openai-codex/gpt-5.6-sol" "$(fm "$pi_out/mmw-planner.md" model)"
check "Pi planner thinking" "high" "$(fm "$pi_out/mmw-planner.md" thinking)"
check "Pi planner async" "true" "$(fm "$pi_out/mmw-planner.md" async)"
check "Pi planner context" "fresh" "$(fm "$pi_out/mmw-planner.md" defaultContext)"
check "Pi planner skill" "mmw-planner" "$(fm "$pi_out/mmw-planner.md" skill)"

check "Pi investigator 走 hosts 覆盖" "xai/grok-4.5" "$(fm "$pi_out/mmw-investigator.md" model)"
check "Pi investigator 无 skill 键" "0" "$(grep -c '^skill:' "$pi_out/mmw-investigator.md" || true)"

check "Pi worker 型号" "openai-codex/gpt-5.6-terra" "$(fm "$pi_out/mmw-worker.md" model)"
check "Pi worker-high-risk 型号" "openai-codex/gpt-5.6-sol" "$(fm "$pi_out/mmw-worker-high-risk.md" model)"
check "Pi reviewer-claude 型号" "xai/grok-4.5" "$(fm "$pi_out/mmw-reviewer-claude.md" model)"

"$MMW" agents materialize --host pi --out "$pi_out" --check
check "Pi --check 与刚写内容一致" "0" "$?"

printf '\nCursor 物化\n'
cu_out="$WORK/cursor-agents"
mkdir -p "$cu_out"
"$MMW" agents materialize --host cursor --out "$cu_out"

check "Cursor planner 型号格式" "gpt-5.6-sol[effort=high]" "$(fm "$cu_out/mmw-planner.md" model)"
check "Cursor planner 后台" "true" "$(fm "$cu_out/mmw-planner.md" is_background)"
check "Cursor planner 可写" "false" "$(fm "$cu_out/mmw-planner.md" readonly)"
check "Cursor investigator 只读" "true" "$(fm "$cu_out/mmw-investigator.md" readonly)"
check "Cursor investigator 基线型号" "gpt-5.6-terra[effort=xhigh]" "$(fm "$cu_out/mmw-investigator.md" model)"
check "Cursor 无 Pi 专有 thinking 键" "0" "$(grep -c '^thinking:' "$cu_out/mmw-planner.md" || true)"

printf '\n--check 能发现漂移\n'
echo '# tamper' >> "$pi_out/mmw-planner.md"
if "$MMW" agents materialize --host pi --out "$pi_out" --check >/dev/null 2>&1; then
  check "篡改后 --check 失败" "fail" "pass"
else
  check "篡改后 --check 失败" "fail" "fail"
fi

printf '\nPi dispatch 只回 agent+cwd\n'
git -C "$WORK" init -q repo
cp "$ROOT/mmw/cli/mmw.default.json" "$WORK/repo/.mmw.json"
printf 'brief\n' > "$WORK/repo/brief.md"
cd "$WORK/repo"
pi_params="$(MMW_HOST=pi "$MMW" dispatch investigator --brief "$WORK/repo/brief.md" | sed -n 's/^params: //p')"
check "Pi params 只有 agent" "mmw-investigator" "$(jq -r '.agent' <<<"$pi_params")"
check "Pi params 无 thinking" "null" "$(jq -r '.thinking // "null"' <<<"$pi_params")"
check "Pi params 无 model" "null" "$(jq -r '.model // "null"' <<<"$pi_params")"
check "Pi params 无 async" "null" "$(jq -r '.async // "null"' <<<"$pi_params")"
check "Pi params 键集合" "agent cwd" "$(jq -r 'keys | sort | join(" ")' <<<"$pi_params")"

printf '\nClaude Code reviewer 仍映射到 mmw-reviewer\n'
claude_params="$(MMW_HOST=claude-code "$MMW" dispatch reviewer-claude --brief "$WORK/repo/brief.md" | sed -n 's/^params: //p')"
check "Claude reviewer subagent_type" "mmw:mmw-reviewer" "$(jq -r '.subagent_type' <<<"$claude_params")"

printf '\n包内 agents-pi 与真源一致\n'
if "$MMW" agents materialize --host pi --check >/dev/null; then
  check "仓库 agents-pi --check" "0" "0"
else
  check "仓库 agents-pi --check" "0" "1"
fi

printf '\n过 %s，失败 %s\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
