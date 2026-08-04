#!/usr/bin/env bash
# 派发参数是宿主会话真正执行 subagent 的合同。
# Pi：策略在原生 agent frontmatter，params 只含 agent+cwd。
# Claude Code：adapter 仍把后台与 effort 写进 params。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MMW="$HERE/../mmw"
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

params() {
  sed -n 's/^params: //p' | jq -c .
}

git -C "$WORK" init -q repo
cp "$HERE/../mmw.default.json" "$WORK/repo/.mmw.json"
printf '只读烟雾测试。\n' > "$WORK/repo/brief.md"
mkdir -p "$WORK/bin"
cat > "$WORK/bin/codex" <<'SH'
#!/usr/bin/env bash
report=""
previous=""
for argument in "$@"; do
  [ "$previous" = "-o" ] && report="$argument"
  previous="$argument"
done
[ -n "${MMW_FAKE_CODEX_ARGS:-}" ] && printf '%s\n' "$@" > "$MMW_FAKE_CODEX_ARGS"
cat >/dev/null
[ -n "$report" ] && printf 'fake codex report\n' > "$report"
SH
chmod +x "$WORK/bin/codex"
cd "$WORK/repo"

printf 'Pi 原生 agent 派发\n'
pi_output="$(MMW_HOST=pi "$MMW" dispatch investigator --brief "$WORK/repo/brief.md")"
pi_params="$(params <<<"$pi_output")"
check "Pi 标 native" "agents-pi" "$(sed -n 's/^native: //p' <<<"$pi_output")"
check "Pi params 只有 agent 与 cwd" "agent cwd" "$(jq -r 'keys | sort | join(" ")' <<<"$pi_params")"
check "Pi agent 名" "mmw-investigator" "$(jq -r '.agent' <<<"$pi_params")"
check "上下文隔离与后台不进 params" "null" "$(jq -r '.context // .async // "null"' <<<"$pi_params")"

# 调查者在两个宿主用不同模型：写在原生 agent / .mmw.json hosts 覆盖里。
printf '\n模型档的宿主覆盖仍由配置持有\n'
check "Pi 调查者 agent 文件存在" "yes" \
  "$([ -f "$HERE/../../agents-pi/mmw-investigator.md" ] && echo yes || echo no)"
check "Pi 调查者 agent 用 Grok" "xai/grok-4.5" \
  "$(sed -n 's/^model: //p' "$HERE/../../agents-pi/mmw-investigator.md" | head -1)"
baseline_agent="$HERE/../../agents-pi/mmw-reviewer-gpt.md"
check "没写覆盖的审查者仍读基线型号" "openai-codex/gpt-5.6-sol" \
  "$(sed -n 's/^model: //p' "$baseline_agent" | head -1)"

printf '\nClaude Code 后台派发\n'
claude_params="$(MMW_HOST=claude-code "$MMW" dispatch reviewer-claude --brief "$WORK/repo/brief.md" | params)"
check "Agent 工具显式在后台运行" "true" "$(jq -r '.run_in_background' <<<"$claude_params")"
check "Claude 审查者仍映射 mmw-reviewer" "mmw:mmw-reviewer" "$(jq -r '.subagent_type' <<<"$claude_params")"

gpt_output="$(PATH="$WORK/bin:$PATH" MMW_HOST=claude-code "$MMW" dispatch investigator --brief "$WORK/repo/brief.md")"
check "GPT 先交回宿主工具参数" "host-tool" "$(sed -n 's/^mode: //p' <<<"$gpt_output")"
check "GPT 由 Bash 工具执行" "Bash" "$(sed -n 's/^tool: //p' <<<"$gpt_output")"
gpt_params="$(params <<<"$gpt_output")"
check "GPT 的 Bash 工具显式在后台运行" "true" "$(jq -r '.run_in_background' <<<"$gpt_params")"
codex_args="$WORK/codex-args"
background_output="$(PATH="$WORK/bin:$PATH" MMW_FAKE_CODEX_ARGS="$codex_args" \
  bash -c "$(jq -r '.command' <<<"$gpt_params")")"
check "Claude Code 的调查者走 Codex 的 gpt-5.6-terra" "gpt-5.6-terra" \
  "$(awk '/^-m$/ { getline; print }' "$codex_args")"
check "Claude Code 的调查者用基线档位" 'model_reasoning_effort="xhigh"' \
  "$(grep '^model_reasoning_effort=' "$codex_args")"
check "后台命令执行后交回报告" "executed" "$(sed -n 's/^mode: //p' <<<"$background_output")"
report="$(sed -n 's/^report: //p' <<<"$background_output")"
check "后台命令写出报告" "fake codex report" "$(cat "$report")"

printf '\n过 %s，失败 %s\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
