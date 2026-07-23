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
expected_skills="$(printf '%s\n' orchestrate release-flow worktree-build worktree-plan worktree-review)"
if [ "$skill_names" = "$expected_skills" ]; then
  ok "安装面只暴露五个 MMW 核心 skills"
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

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
