#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

FRAG="$PLUGIN/build/fragments/locate-mmw.md"
[ -f "$FRAG" ] || { echo "missing locate fragment"; exit 1; }
grep -q 'MMW_ENGINE_ROOT\|multi-model-workflow-engine\|cursor-plugin' "$FRAG" \
  && ok "locate mentions Cursor engine install" || no "locate Cursor"
! grep -qE '\.pi/agent/settings|pi-plugin/\?\$|\.factory/plugins|plugins/local' "$FRAG" \
  && ok "locate does not probe foreign hosts or plugins/local" || no "foreign probe"

# commands exist + Cursor frontmatter
n=$(ls "$PLUGIN/commands"/*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$n" = 11 ] && ok "11 commands" || no "commands count=$n"

expected='approve-design attended force-validate gather-context progress reassess replan-remaining rescope side-finding skip-current unattended'
for name in $expected; do
  f="$PLUGIN/commands/$name.md"
  [ -f "$f" ] || { no "missing $name.md"; continue; }
  awk '
    BEGIN { in_fm=0; name=""; desc="" }
    /^---[[:space:]]*$/ { if (++in_fm == 1) next; exit }
    in_fm == 1 && $1 ~ /^name:/ { sub(/^name:[[:space:]]*/, ""); name=$0 }
    in_fm == 1 && $1 ~ /^description:/ { sub(/^description:[[:space:]]*/, ""); desc=$0 }
    END {
      if (name == "'"$name"'" && length(desc) > 0) exit 0
      exit 1
    }
  ' "$f" && ok "frontmatter $name" || no "frontmatter $name (need name+description)"
done

[ -x "$PLUGIN/scripts/install-local-surface.sh" ] \
  && ok "install-local-surface.sh present" || no "missing install-local-surface.sh"

INSTALL="$PLUGIN/scripts/install-local-surface.sh"
SANDBOX="$(mktemp -d)"
HOME_SB="$SANDBOX/home"
mkdir -p "$HOME_SB/.cursor"
HOOKS_JSON="$HOME_SB/.cursor/hooks.json"
MCP_JSON="$HOME_SB/.cursor/mcp.json"
printf '%s\n' '{"version":1,"hooks":{}}' > "$HOOKS_JSON"
printf '%s\n' '{"mcpServers":{"keep-me":{"command":"true"}}}' > "$MCP_JSON"
mkdir -p "$HOME_SB/.cursor/commands"
echo stale-cmd > "$HOME_SB/.cursor/commands/approve-design.md"

if HOME="$HOME_SB" \
   CURSOR_USER_AGENTS="$HOME_SB/.cursor/agents" \
   CURSOR_USER_SKILLS="$HOME_SB/.cursor/skills" \
   CURSOR_USER_COMMANDS="$HOME_SB/.cursor/commands" \
   CURSOR_USER_RULES="$HOME_SB/.cursor/rules" \
   CURSOR_USER_HOOKS_DIR="$HOME_SB/.cursor/hooks" \
   CURSOR_USER_HOOKS="$HOOKS_JSON" \
   CURSOR_USER_MCP="$MCP_JSON" \
   MMW_ENGINE_ROOT="$HOME_SB/.cursor/multi-model-workflow-engine" \
   MMW_INSTALL_SKIP_UV=1 \
   bash "$INSTALL" >/dev/null; then
  [ -f "$HOME_SB/.cursor/agents/advisor.md" ] \
    && [ -f "$HOME_SB/.cursor/skills/orchestrate/SKILL.md" ] \
    && [ -f "$HOME_SB/.cursor/commands/approve-design.md" ] \
    && [ ! -L "$HOME_SB/.cursor/commands/approve-design.md" ] \
    && [ -f "$HOME_SB/.cursor/rules/retrieval-priority.mdc" ] \
    && [ -x "$HOME_SB/.cursor/hooks/session-triage.sh" ] \
    && [ -f "$HOME_SB/.cursor/multi-model-workflow-engine/scripts/mmw.sh" ] \
    && [ -f "$HOME_SB/.cursor/multi-model-workflow-engine/.cursor-plugin/plugin.json" ] \
    && ok "install copies native surface + engine" || no "install native surface incomplete"
  jq -e '.hooks.sessionStart' "$HOOKS_JSON" >/dev/null \
    && grep -q "$HOME_SB/.cursor/hooks/session-triage.sh" "$HOOKS_JSON" \
    && ok "install merges hooks to user hooks dir" || no "hooks merge broken"
  jq -e '.mcpServers.serena and .mcpServers["keep-me"]' "$MCP_JSON" >/dev/null \
    && grep -q 'multi-model-workflow-engine/scripts/serena-mcp.sh' "$MCP_JSON" \
    && ok "install merges mcp keeping user servers" || no "mcp merge broken"
  # 幂等
  HOME="$HOME_SB" \
    CURSOR_USER_AGENTS="$HOME_SB/.cursor/agents" \
    CURSOR_USER_SKILLS="$HOME_SB/.cursor/skills" \
    CURSOR_USER_COMMANDS="$HOME_SB/.cursor/commands" \
    CURSOR_USER_RULES="$HOME_SB/.cursor/rules" \
    CURSOR_USER_HOOKS_DIR="$HOME_SB/.cursor/hooks" \
    CURSOR_USER_HOOKS="$HOOKS_JSON" \
    CURSOR_USER_MCP="$MCP_JSON" \
    MMW_ENGINE_ROOT="$HOME_SB/.cursor/multi-model-workflow-engine" \
    MMW_INSTALL_SKIP_UV=1 \
    bash "$INSTALL" >/dev/null
  [ -f "$HOME_SB/.cursor/agents/pack-executor.md" ] \
    && ok "install native idempotent" || no "install not idempotent"
else
  no "install-local-surface failed in sandbox"
fi
rm -rf "$SANDBOX"

jq -e '.commands == "./commands/"' "$PLUGIN/.cursor-plugin/plugin.json" >/dev/null \
  && ok "plugin.json declares commands" || no "plugin.json commands"

! rg -n 'enter_worktree\(\{' "$PLUGIN" --glob '!**/scripts/tests/**' >/dev/null \
  && ok "no enter_worktree({...}) calls" || no "enter_worktree({...}) still present"
! rg -n '(^|[^_])background:true' "$PLUGIN/scripts/investigate.sh" >/dev/null \
  && rg -n 'run_in_background:true' "$PLUGIN/scripts/investigate.sh" >/dev/null \
  && ok "investigate DISPATCH uses run_in_background" || no "investigate DISPATCH param"
! rg -n 'advisor\(\)|零参数' "$PLUGIN/agents/advisor.md" "$PLUGIN/skills/orchestrate" >/dev/null \
  && ok "no advisor() zero-arg lies" || no "advisor zero-arg residue"

exit "$fail"
