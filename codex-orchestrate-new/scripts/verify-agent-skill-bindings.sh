#!/usr/bin/env bash
# Verify required per-agent skill bindings for Codex custom agents.
set -euo pipefail

PLUGIN_DIR="${1:-codex-orchestrate-new}"
AGENT_DIR="${2:-$PLUGIN_DIR/agents}"
CHECK_INSTALLED=0
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

if [[ "${2:-}" == "--check-installed" ]]; then
  AGENT_DIR="$PLUGIN_DIR/agents"
  CHECK_INSTALLED=1
elif [[ "${3:-}" == "--check-installed" ]]; then
  CHECK_INSTALLED=1
fi

fail_count=0

fail() {
  echo "  ✗ $*"
  fail_count=$((fail_count + 1))
}

pass() {
  echo "  ✓ $*"
}

skill_path() {
  local skill="$1"
  case "$skill" in
    ponytail)
      printf '%s/plugins/cache/ponytail/ponytail/4.7.0/skills/ponytail/SKILL.md\n' "$CODEX_HOME"
      ;;
    ponytail-review)
      printf '%s/plugins/cache/ponytail/ponytail/4.7.0/skills/ponytail-review/SKILL.md\n' "$CODEX_HOME"
      ;;
    tdd|diagnose|prototype|improve-codebase-architecture)
      printf '%s/.agents/upstreams/mattpocock-skills/skills/engineering/%s/SKILL.md\n' "$HOME" "$skill"
      ;;
    frontend-testing-debugging)
      printf '%s/plugins/cache/openai-curated/build-web-apps/43313cc9/skills/frontend-testing-debugging/SKILL.md\n' "$CODEX_HOME"
      ;;
    *)
      return 1
      ;;
  esac
}

has_skill_binding() {
  local file="$1"
  local expected_path="$2"
  awk -v expected_path="$expected_path" '
    BEGIN { RS = "\\[\\[skills\\.config\\]\\]"; found = 0 }
    NR > 1 && index($0, "path = \"" expected_path "\"") && index($0, "enabled = true") { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "$file"
}

check_agent_skill() {
  local agent="$1"
  local skill="$2"
  local file="$AGENT_DIR/${agent}.toml"
  if [[ ! -f "$file" ]]; then
    fail "agent TOML missing: $file"
    return
  fi
  expected_path="$(skill_path "$skill")"
  if has_skill_binding "$file" "$expected_path"; then
    pass "$agent binds skill path: $skill"
  else
    fail "$agent missing required skill binding path for $skill: $expected_path"
  fi
}

check_call_section() {
  local agent="$1"
  local file="$AGENT_DIR/${agent}.toml"
  if grep -q 'Skill 调用' "$file"; then
    pass "$agent documents skill call timing"
  else
    fail "$agent missing Skill 调用 section"
  fi
}

skill_installed() {
  local skill="$1"
  local expected_path
  expected_path="$(skill_path "$skill")"
  test -f "$expected_path"
}

check_installed_skill() {
  local skill="$1"
  if skill_installed "$skill"; then
    pass "required skill installed: $skill"
  else
    fail "required skill not installed or not discoverable: $skill"
  fi
}

required_bindings=(
  "pack_executor:ponytail"
  "pack_executor:tdd"
  "pack_executor:diagnose"
  "pack_executor:prototype"
  "pack_executor:frontend-testing-debugging"
  "complex_pack_executor:ponytail"
  "complex_pack_executor:tdd"
  "complex_pack_executor:diagnose"
  "complex_pack_executor:improve-codebase-architecture"
  "complex_pack_executor:prototype"
  "complex_pack_executor:frontend-testing-debugging"
  "root_cause_analyst:ponytail"
  "root_cause_analyst:diagnose"
  "root_cause_analyst:tdd"
  "plan_writer:ponytail"
  "plan_writer:improve-codebase-architecture"
  "codex_reviewer:ponytail-review"
  "codex_planning_reviewer:ponytail"
  "codex_planning_reviewer:improve-codebase-architecture"
  "code_explorer:diagnose"
  "complex_code_explorer:improve-codebase-architecture"
  "complex_code_explorer:diagnose"
)

agents_with_skill_sections=(
  pack_executor
  complex_pack_executor
  root_cause_analyst
  plan_writer
  codex_reviewer
  codex_planning_reviewer
  code_explorer
  complex_code_explorer
)

for entry in "${required_bindings[@]}"; do
  agent="${entry%%:*}"
  skill="${entry#*:}"
  check_agent_skill "$agent" "$skill"
done

for agent in "${agents_with_skill_sections[@]}"; do
  check_call_section "$agent"
done

if [[ "$CHECK_INSTALLED" -eq 1 ]]; then
  checked=""
  for entry in "${required_bindings[@]}"; do
    skill="${entry#*:}"
    case " $checked " in
      *" $skill "*) continue ;;
    esac
    checked="$checked $skill"
    check_installed_skill "$skill"
  done
fi

if [[ "$fail_count" -gt 0 ]]; then
  echo "Agent skill binding verification failed: $fail_count issue(s)"
  exit 1
fi

echo "Agent skill binding verification passed"
