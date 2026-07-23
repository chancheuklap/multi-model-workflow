#!/usr/bin/env bash
# Codex 控制 wrapper：11 个真实入口、显式调用边界和薄接线。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0
fail=0
ok() { echo "  PASS: $1"; pass=$((pass + 1)); }
no() { echo "  FAIL: $1"; fail=$((fail + 1)); }

controls=(
  approve-design attended force-validate gather-context progress reassess
  replan-remaining rescope side-finding skip-current unattended
)
explicit=(
  approve-design replan-remaining rescope side-finding skip-current unattended
)

is_explicit() {
  local candidate="$1" item
  for item in "${explicit[@]}"; do
    [ "$item" = "$candidate" ] && return 0
  done
  return 1
}

echo "=== test_control_skills.sh ==="

missing=()
for control in "${controls[@]}"; do
  [ -f "$PLUGIN_DIR/skills/$control/SKILL.md" ] || missing+=("$control/SKILL.md")
  [ -f "$PLUGIN_DIR/skills/$control/agents/openai.yaml" ] || missing+=("$control/agents/openai.yaml")
done
[ "${#missing[@]}" -eq 0 ] \
  && ok "11 个控制入口都有 SKILL 和 Codex metadata" \
  || no "控制入口缺文件:${missing[*]}"

bad_policy=()
for control in "${controls[@]}"; do
  metadata="$PLUGIN_DIR/skills/$control/agents/openai.yaml"
  [ -f "$metadata" ] || continue
  actual="$(sed -n 's/^[[:space:]]*allow_implicit_invocation:[[:space:]]*//p' "$metadata")"
  expected=true
  is_explicit "$control" && expected=false
  [ "$actual" = "$expected" ] || bad_policy+=("$control=$actual(expected $expected)")
done
[ "${#bad_policy[@]}" -eq 0 ] \
  && ok "需要用户明确触发的 6 个入口禁止隐式调用" \
  || no "控制入口 invocation policy 错误:${bad_policy[*]}"

bad_surface=()
for control in "${controls[@]}"; do
  skill="$PLUGIN_DIR/skills/$control/SKILL.md"
  metadata="$PLUGIN_DIR/skills/$control/agents/openai.yaml"
  [ -f "$skill" ] && [ -f "$metadata" ] || continue
  grep -q "^name: $control$" "$skill" || bad_surface+=("$control:name")
  grep -q '^description:' "$skill" || bad_surface+=("$control:description")
  grep -q 'display_name:' "$metadata" || bad_surface+=("$control:display")
  [ "$(wc -l <"$skill" | tr -d ' ')" -le 48 ] || bad_surface+=("$control:not-thin")
done
[ "${#bad_surface[@]}" -eq 0 ] \
  && ok "控制入口是可发现的薄 wrapper" \
  || no "控制入口表面错误:${bad_surface[*]}"

if rg -n '\.claude|CLAUDE_PLUGIN_ROOT|\.pi|pi-plugin|\.factory|droid-plugin|disable-model-invocation|AskUserQuestion' \
  "${controls[@]/#/$PLUGIN_DIR/skills/}" >/dev/null; then
  no "Codex 控制入口残留其他宿主接线"
else
  ok "控制入口没有 Claude、pi 或 Droid 接线"
fi

grep -q '"$MMW" approve' "$PLUGIN_DIR/skills/approve-design/SKILL.md" \
  && grep -q '"$MMW" unattended enter' "$PLUGIN_DIR/skills/unattended/SKILL.md" \
  && grep -q '"$MMW" handoff --conclusion needs-redirection --to-phase plan' \
    "$PLUGIN_DIR/skills/replan-remaining/SKILL.md" \
  && grep -q '"$MMW" task scope' "$PLUGIN_DIR/skills/rescope/SKILL.md" \
  && grep -q '"$MMW" progress render --stdout' "$PLUGIN_DIR/skills/progress/SKILL.md" \
  && ok "关键 wrapper 仍调用原有 MMW 机械动作" \
  || no "wrapper 绕开或漏掉原有 MMW 动作"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
