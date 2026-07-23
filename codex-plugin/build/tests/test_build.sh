#!/usr/bin/env bash
# Codex plugin 构建与安装表面的公开合同。
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$HERE/../.." && pwd)"
REPO_ROOT="$(cd "$PLUGIN_DIR/.." && pwd)"
MANIFEST="$PLUGIN_DIR/.codex-plugin/plugin.json"
MARKETPLACE="$REPO_ROOT/.agents/plugins/marketplace.json"

pass=0
fail=0
ok() { echo "  PASS: $1"; pass=$((pass + 1)); }
no() { echo "  FAIL: $1"; fail=$((fail + 1)); }

echo "=== test_build.sh ==="

if jq -e '
  .name == "multi-model-workflow"
  and (.version | test("^[0-9]+\\.[0-9]+\\.[0-9]+$"))
  and .skills == "./skills/"
  and .hooks == "./hooks/hooks.json"
' "$MANIFEST" >/dev/null 2>&1; then
  ok "Codex plugin manifest 声明稳定标识、版本和 skill 入口"
else
  no "Codex plugin manifest 不完整"
fi

if jq -e --arg path "./codex-plugin" '
  .name == "multi-model-workflow-local"
  and (.interface.displayName | length > 0)
  and any(.plugins[];
    .name == "multi-model-workflow"
    and .source.source == "local"
    and .source.path == $path
    and .policy.installation == "AVAILABLE"
    and .policy.authentication == "ON_INSTALL"
    and (.category | length > 0)
  )
' "$MARKETPLACE" >/dev/null 2>&1; then
  ok "仓库 marketplace 可定位 Codex plugin"
else
  no "仓库 marketplace 未登记 Codex plugin"
fi

skill_names="$(
  find "$PLUGIN_DIR/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -print 2>/dev/null \
    | while IFS= read -r skill; do
        sed -n 's/^name:[[:space:]]*//p' "$skill" | head -1
      done \
    | sort
)"
expected_skills="$(printf '%s\n' \
  approve-design attended force-validate gather-context orchestrate progress reassess \
  release-flow replan-remaining rescope side-finding skip-current unattended \
  worktree-build worktree-plan worktree-review | sort)"
if [ "$skill_names" = "$expected_skills" ]; then
  ok "安装面暴露五个核心 skills 和 11 个控制 wrappers"
else
  no "Codex plugin skill surface 不符"
fi

if [ ! -e "$PLUGIN_DIR/.codex/agents" ] \
  && ! jq -e 'has("agents")' "$MANIFEST" >/dev/null 2>&1; then
  ok "Codex plugin 没有 custom agents"
else
  no "Codex plugin 不得安装 custom agents"
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export CODEX_HOME="$TMP/codex-home"
mkdir -p "$CODEX_HOME"

if codex plugin marketplace add "$REPO_ROOT" --json >/dev/null 2>&1 \
  && codex plugin list --marketplace multi-model-workflow-local --available --json \
    | jq -e '.. | objects | select(.name? == "multi-model-workflow")' >/dev/null; then
  ok "Codex CLI 能从仓库 marketplace 发现 plugin"
else
  no "Codex CLI 无法从仓库 marketplace 发现 plugin"
fi

install_json="$(codex plugin add multi-model-workflow@multi-model-workflow-local --json 2>/dev/null || true)"
installed_path="$(jq -r '.installedPath // empty' <<<"$install_json")"
if [ -n "$installed_path" ] \
  && [ -f "$installed_path/.codex-plugin/plugin.json" ] \
  && [ "$(cd "$installed_path" && pwd -P)" != "$(cd "$PLUGIN_DIR" && pwd -P)" ]; then
  ok "Codex 安装后从独立 cache 加载 plugin"
else
  no "Codex plugin 没有安装到独立 cache"
fi

cached_topic='{"topic":"cache-check","findings":[{"claim":"loaded from cache","locator":"src/app.ts:1","confidence":"high"}],"summary":"ok","gaps":[]}'
if [ -f "$installed_path/agents-roster/investigate-topic.md" ] \
  && [ -f "$installed_path/agents-roster/investigate-synthesizer.md" ] \
  && printf '%s\n' "$cached_topic" \
    | bash "$installed_path/scripts/investigate-contract.sh" topic \
        --mode internal --expected-topic cache-check \
    | jq -e '.findings|length==1' >/dev/null 2>&1; then
  ok "安装 cache 内的 native investigate prompt 与合同可直接运行"
else
  no "安装 cache 缺 native investigate 运行面"
fi

if [ -f "$installed_path/scripts/worker.sh" ] \
  && [ -f "$installed_path/skills/worktree-plan/SKILL.md" ] \
  && [ -f "$installed_path/skills/worktree-build/SKILL.md" ] \
  && bash -n "$installed_path/scripts/worker.sh" \
  && grep -q 'spawn_agent' "$installed_path/scripts/worker.sh" \
  && ! grep -qiE 'codex exec|note-run-id|PI_CODING_AGENT_DIR' "$installed_path/scripts/worker.sh"; then
  ok "安装 cache 内的 native plan/build worker 可直接运行"
else
  no "安装 cache 缺 native plan/build worker 运行面"
fi

if [ -f "$installed_path/scripts/review.sh" ] \
  && [ -f "$installed_path/scripts/second-review.sh" ] \
  && [ -f "$installed_path/agents-roster/reviewer.md" ] \
  && bash -n "$installed_path/scripts/review.sh" "$installed_path/scripts/second-review.sh" \
  && grep -q 'spawn_agent' "$installed_path/scripts/review.sh" \
  && ! grep -qE 'Claude|Gemini|codex exec' "$installed_path/scripts/second-review.sh"; then
  ok "安装 cache 内的 native/second review 运行面完整"
else
  no "安装 cache 缺 review 运行面"
fi

if [ -f "$installed_path/scripts/package-phase.sh" ] \
  && [ -f "$installed_path/scripts/release-flow.sh" ] \
  && [ -f "$installed_path/scripts/release_contracts.py" ] \
  && [ -f "$installed_path/scripts/release_templates/windows_core_exe.ps1.tmpl" ] \
  && [ -f "$installed_path/skills/release-flow/references/drive-loop.md" ] \
  && bash -n "$installed_path/scripts/package-phase.sh" "$installed_path/scripts/release-flow.sh" \
  && grep -q 'NATIVE-REPAIR-READY' "$installed_path/scripts/release-flow.sh" \
  && grep -q 'spawn_agent(fork_turns="none")' "$installed_path/skills/release-flow/references/drive-loop.md" \
  && ! grep -q 'fix_executor' "$installed_path/scripts/release-flow.sh"; then
  ok "安装 cache 内的 package/release 使用 Codex 原生 P1 修复"
else
  no "安装 cache 缺 package/release 或仍执行外部修复模型"
fi

if [ -f "$installed_path/hooks/hooks.json" ] \
  && [ -f "$installed_path/hooks/guard-redline.sh" ] \
  && [ -f "$installed_path/hooks/record-step.sh" ] \
  && jq -e '.hooks | has("SessionStart") and has("PreToolUse") and has("PostToolUse")' \
    "$installed_path/hooks/hooks.json" >/dev/null \
  && [ -f "$installed_path/skills/approve-design/agents/openai.yaml" ]; then
  ok "安装 cache 内的控制 wrappers 与 hooks 完整"
else
  no "安装 cache 缺控制 wrappers 或 hooks"
fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
