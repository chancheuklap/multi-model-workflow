#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

[ -f "$PLUGIN/.cursor-plugin/plugin.json" ] && ok "Cursor manifest exists" || no "Cursor manifest"
[ ! -d "$PLUGIN/extensions" ] && ok "no Pi extensions" || no "unexpected extensions"
[ ! -d "$PLUGIN/workflows" ] && ok "no workflows dir" || no "unexpected workflows"
[ ! -f "$PLUGIN/scripts/render_agent_prompts.py" ] && ok "no render_agent_prompts" || no "render script leaked"
[ ! -f "$PLUGIN/scripts/lib/droid-exec.sh" ] && ok "no droid-exec" || no "droid-exec leaked"
[ ! -f "$PLUGIN/agents/decision-advisor.md" ] && ok "no decision-advisor" || no "decision-advisor leaked"

[ "$(jq -r .name "$PLUGIN/.cursor-plugin/plugin.json")" = multi-model-workflow-cursor ] &&
  ok "dedicated plugin identity" || no "plugin identity"

jq -e '
  .mcpServers == "./mcp.json"
  and .rules == "./rules/"
  and (.variables | not)
' "$PLUGIN/.cursor-plugin/plugin.json" >/dev/null \
  && ok "plugin declares mcpServers + rules without Configure variables" || no "plugin mcp/rules wiring"

[ -f "$PLUGIN/rules/retrieval-priority.mdc" ] \
  && grep -q 'alwaysApply: true' "$PLUGIN/rules/retrieval-priority.mdc" \
  && grep -q 'Graphify MCP' "$PLUGIN/rules/retrieval-priority.mdc" \
  && ok "Always Apply retrieval rule present" || no "retrieval rule"

grep -q 'skills/graphify/scripts/graphify_ensure\|插件内 graphify ensure\|plugin ensure' \
  "$PLUGIN/scripts/lib/runtime.sh" \
  && grep -qE 'Graphify MCP|ensure' "$PLUGIN/skills/orchestrate/references/retrieval-doctrine.md" \
  && ok "runtime + doctrine ensure Graphify" || no "Graphify ensure wiring"

jq -e '
  .mcpServers.serena.command == "bash"
  and (.mcpServers.serena.args | length == 2)
  and .mcpServers.serena.args[0] == "-c"
  and (.mcpServers.serena.args[1] | test("serena-mcp\\.sh"))
  and (.mcpServers.serena.args[1] | test("\\$HOME"))
  and .mcpServers.serena.env.SERENA_PROJECT == "${workspaceFolder}"
  and .mcpServers.serena.env.MMW_SERENA_LAUNCHER == "v3-bash-home"
  and .mcpServers.graphify.command == "bash"
  and (.mcpServers.graphify.args | length == 2)
  and .mcpServers.graphify.args[0] == "-c"
  and (.mcpServers.graphify.args[1] | test("graphify-mcp\\.sh"))
  and (.mcpServers.graphify.args[1] | test("\\$HOME"))
  and .mcpServers.graphify.env.GRAPHIFY_PROJECT == "${workspaceFolder}"
  and .mcpServers.graphify.env.MMW_GRAPHIFY_LAUNCHER == "v1-bash-home"
  and .mcpServers.context7.command == "npx"
  and (.mcpServers.context7.args | index("@upstash/context7-mcp"))
  and .mcpServers.context7.env.CONTEXT7_API_KEY == "${env:CONTEXT7_API_KEY}"
  and .mcpServers.context7.envFile == "${userHome}/.cursor/context7.env"
' "$PLUGIN/mcp.json" >/dev/null \
  && ok "mcp.json ships serena + graphify + context7" || no "mcp.json servers"

# 禁止相对 ./scripts 与 CURSOR_PLUGIN_ROOT（MCP 侧展开不可靠）
! jq -e '.. | strings | select(test("(^|[ \"])\\\\./scripts/|CURSOR_PLUGIN_ROOT"))' "$PLUGIN/mcp.json" >/dev/null \
  && ok "mcp.json uses bash+HOME launcher" || no "mcp.json path contract broken"

# 禁止从其他宿主目录取 MCP / Serena 配置
! grep -R -nE '~/?\.pi|/\\.pi/|pi-readonly|context7\\.local\\.json|~/?\.agents/skills' \
  "$PLUGIN/mcp.json" "$PLUGIN/scripts/serena-mcp.sh" "$PLUGIN/scripts/graphify-mcp.sh" "$PLUGIN/config/serena" \
  >/dev/null 2>&1 \
  && ok "MCP wiring has no foreign-host skill coupling" || no "MCP probes foreign hosts"

[ -f "$PLUGIN/config/serena/cursor-readonly.yml" ] \
  && [ -x "$PLUGIN/scripts/serena-mcp.sh" ] \
  && [ -x "$PLUGIN/scripts/graphify-mcp.sh" ] \
  && [ -f "$PLUGIN/scripts/lib/uv-tool-maintain.sh" ] \
  && [ -f "$PLUGIN/config/retrieval/contracts.json" ] \
  && [ -f "$PLUGIN/skills/serena/SKILL.md" ] \
  && [ -f "$PLUGIN/skills/graphify/SKILL.md" ] \
  && [ -f "$PLUGIN/skills/graphify/scripts/graphify_mcp.py" ] \
  && [ -f "$PLUGIN/skills/graphify/scripts/graphify_ensure.py" ] \
  && ok "Serena + Graphify launchers/skills/contracts present" || no "retrieval launchers"

grep -q 'mmw_maintain_serena' "$PLUGIN/scripts/serena-mcp.sh" \
  && grep -q 'mmw_maintain_graphify' "$PLUGIN/scripts/graphify-mcp.sh" \
  && grep -q 'skills/graphify/scripts/graphify_mcp.py' "$PLUGIN/scripts/graphify-mcp.sh" \
  && ok "launchers maintain+plugin-local Graphify wrapper" || no "launcher maintain wiring"

! grep -q 'link_skill' "$PLUGIN/scripts/install-local-surface.sh" \
  && ! grep -q 'CLAUDE_GRAPHIFY' "$PLUGIN/scripts/install-local-surface.sh" \
  && ! grep -q 'AGENTS_SKILLS' "$PLUGIN/scripts/install-local-surface.sh" \
  && grep -q 'serena-agent' "$PLUGIN/scripts/install-local-surface.sh" \
  && ok "install-local-surface stays Cursor-local (no cross-harness skill links)" || no "install surface scope"

grep -q 'mcp:graphify/graphify' "$PLUGIN/agents/investigate-topic.md" \
  && grep -q 'mcp:graphify/graphify' "$PLUGIN/agents/code-explorer.md" \
  && ok "investigate-topic + code-explorer have Graphify MCP" || no "agents Graphify tools"

grep -q 'mcp:context7/resolve-library-id' "$PLUGIN/agents/investigate-topic.md" \
  && grep -q 'mcp:context7/query-docs' "$PLUGIN/agents/investigate-topic.md" \
  && ok "investigate-topic has Context7 tools" || no "investigate-topic Context7"

jq -e '.hooks.sessionStart and .hooks.beforeShellExecution and .hooks.afterShellExecution' \
  "$PLUGIN/hooks/hooks.json" >/dev/null && ok "Cursor hook events" || no "hook events"

for d in investigate-topic investigate-synthesizer code-explorer plan-writer pack-executor pack-executor-capable \
  reviewer-design-a reviewer-design-b reviewer-plan-a reviewer-plan-b reviewer-final-a reviewer-final-b advisor; do
  file="$PLUGIN/agents/$d.md"
  [ -f "$file" ] || { no "missing agent $d"; continue; }
  grep -q '^description: ' "$file" || no "missing description $d"
  grep -q '^model: ' "$file" || no "missing model $d"
  ! grep -q '^thinking:' "$file" || no "stale thinking field in $d (use model[effort=…])"
  ! grep -q '^is_background_agent:' "$file" || no "stale is_background_agent in $d (use is_background)"
  grep -qE '^is_background: (true|false)$' "$file" || no "missing/invalid is_background $d"
  ! grep -qi 'Kimi K3' "$file" || no "stale Kimi label in $d"
  ! grep -q 'contact_supervisor' "$file" || no "contact_supervisor in $d"
  ! grep -q 'mmw:fragments BEGIN' "$file" || no "fragment block in $d"
done
[ "$fail" -eq 0 ] && ok "all role agents present"

# mmw_agent_model + 官方 effort 语法
export CURSOR_PLUGIN_ROOT="$PLUGIN"
# shellcheck disable=SC1091
. "$PLUGIN/scripts/lib/runtime.sh"
[ "$(mmw_agent_model advisor)" = "claude-opus-5[effort=high]" ] \
  && ok "advisor model uses [effort=high]" || no "advisor effort model"
[ "$(mmw_agent_model pack-executor)" = "composer-2.5" ] \
  && ok "composer has no effort param" || no "pack-executor bare model"
! grep -rq '^thinking:' "$PLUGIN/agents" \
  && ok "no thinking: frontmatter (Cursor ignores it)" || no "stale thinking fields"

grep -q 'advisor-strategy pattern' "$PLUGIN/agents/advisor.md" \
  && ok "advisor system prompt present" || no "advisor prompt"

grep -q 'AskQuestion' "$PLUGIN/scripts/lib/runtime.sh" \
  && grep -q 'cursor-task' "$PLUGIN/scripts/lib/runtime.sh" \
  && ok "runtime Cursor constants" || no "runtime constants"

grep -q 'cmd_adopt' "$PLUGIN/scripts/prepare.sh" \
  && ok "task adopt exists" || no "task adopt"

grep -q 'investigate)' "$PLUGIN/scripts/mmw.sh" \
  && ok "mmw investigate wired" || no "investigate wire"

# locate must not probe foreign hosts
! grep -qE '\.pi/agent/settings|\.factory/plugins|claude-plugin' \
  "$PLUGIN/build/fragments/locate-mmw.md" \
  && ok "locate is Cursor-only" || no "locate probes foreign hosts"

exit "$fail"
