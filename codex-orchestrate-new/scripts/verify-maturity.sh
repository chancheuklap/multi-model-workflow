#!/usr/bin/env bash
# Codex clean-migration maturity gate.
set -euo pipefail

PLUGIN_DIR="${1:-codex-orchestrate-new}"
PASS=0
FAIL=0

check() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    printf '  ✓ %s\n' "$name"
    PASS=$((PASS + 1))
  else
    printf '  ✗ %s\n' "$name"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Codex Orchestrate Clean Migration Verification ==="

echo
echo "## Manifest + marketplace shape"
check "Codex manifest exists" test -f "$PLUGIN_DIR/.codex-plugin/plugin.json"
check "Codex manifest valid JSON" python3 -m json.tool "$PLUGIN_DIR/.codex-plugin/plugin.json"
check "manifest declares skills path" jq -e '.skills == "./skills/" or .skills == "./skills"' "$PLUGIN_DIR/.codex-plugin/plugin.json"
check "manifest declares root hooks.json" jq -e '.hooks == "./hooks.json"' "$PLUGIN_DIR/.codex-plugin/plugin.json"
check "root hooks.json valid" python3 -m json.tool "$PLUGIN_DIR/hooks.json"

echo
echo "## Build + schemas"
check "build check passes" bash "$PLUGIN_DIR/build/build.sh" --check --plugin-dir "$PLUGIN_DIR"
for f in workflow-state-v1.json execution-state-v1.json dispatch-envelope-v1.json routes-v1.json routes-v1.schema.json plan-return-v1.json open-items-v1.json pack-returns-v1.json merge-brief-v1.json; do
  check "schema valid: $f" python3 -m json.tool "$PLUGIN_DIR/state-schema/$f"
done

echo
echo "## Codex agents"
for agent in pack_executor complex_pack_executor plan_writer codex_reviewer root_cause_analyst code_explorer complex_code_explorer; do
  check "agent TOML exists: $agent" test -f "$PLUGIN_DIR/agents/${agent}.toml"
  check "sync script registers: $agent" grep -q "\"$agent\"" "$PLUGIN_DIR/agents/sync-agents.sh"
done
check "no legacy markdown agent configs" bash -c "! find '$PLUGIN_DIR/agents' -maxdepth 1 -type f -name '*.md' ! -name 'persona.md' ! -name 'agents.overrides.md' | grep -q ."
check "docs_worker not registered by clean migration" bash -c "! grep -q 'docs_worker' '$PLUGIN_DIR/agents/sync-agents.sh'"
check "plan_writer can write plans" grep -q 'sandbox_mode = "workspace-write"' "$PLUGIN_DIR/agents/plan_writer.toml"
check "Codex agent TOML generated anchors are checked" grep -q -- '-name "\*.toml"' "$PLUGIN_DIR/build/build.sh"
check "all voice-directive variants resolve" bash -c 'for v in pack_executor complex_pack_executor plan_writer code_explorer complex_code_explorer root_cause_analyst discovery execution plan-writing final-review multi-pr-merge workflow; do grep -q "^\[variant=$v\]" "$1"; done' _ "$PLUGIN_DIR/build/templates/voice-directive.md.tmpl"

echo
echo "## Codex-native dispatch contracts"
check "review dispatch uses codex_reviewer" grep -q 'codex_reviewer' "$PLUGIN_DIR/skills/_shared/review-dispatch.md"
check "review dispatch mentions spawn_agent" grep -q 'spawn_agent' "$PLUGIN_DIR/skills/_shared/review-dispatch.md"
check "review completion counts budget" grep -q 'budget increment-review' "$PLUGIN_DIR/scripts/complete-review-dispatch.sh"
check "repair cap enforced in dispatch-review" grep -q 'validate_repair_round_cap' "$PLUGIN_DIR/scripts/dispatch-review.sh"
check "execution skill uses Plan worker spawn" grep -q 'spawn_agent' "$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md"
check "execution skill has no execution carrier selection" bash -c "! grep -q '执行载体选择\\|execution carrier selection' '$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md'"
check "parse-envelope allows ad-hoc review" grep -q 'baseline|ad-hoc' "$PLUGIN_DIR/hooks/lib/parse-envelope.sh"
check "schema allows ad-hoc review" jq -e '.properties.review_intent.oneOf[0].enum | index("ad-hoc")' "$PLUGIN_DIR/state-schema/dispatch-envelope-v1.json"
check "schema covers route-worker phases" jq -e '(.properties.phase.enum | index("bug-investigation")) and (.properties.phase.enum | index("direct-repair")) and (.properties.phase.enum | index("multi-pr-merge"))' "$PLUGIN_DIR/state-schema/dispatch-envelope-v1.json"
check "multi-pr route-worker runs dedicated gate" grep -q 'validate-multi-pr-dispatch.sh' "$PLUGIN_DIR/scripts/dispatch-route-worker.sh"
check "resume repair uses Codex target field" grep -q 'send_input({' "$PLUGIN_DIR/build/templates/send-input-resume.md.tmpl"
check "resume repair does not use legacy to field" bash -c "! grep -q 'to: \"<' '$PLUGIN_DIR/build/templates/send-input-resume.md.tmpl'"
check "execution dispatch docs keep plan and manifest validators" bash -c "grep -q 'validate-plan-dispatch.sh' '$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md' && grep -q 'validate-pack-manifest.sh' '$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md'"

echo
echo "## Hooks"
check "SessionStart uses .codex-plugin manifest" grep -q '.codex-plugin/plugin.json' "$PLUGIN_DIR/hooks/session-start.sh"
check "hooks use PLUGIN_ROOT commands" grep -q '\${PLUGIN_ROOT}' "$PLUGIN_DIR/hooks.json"
check "payload helper exists" test -f "$PLUGIN_DIR/hooks/lib/payload.sh"
check "guard-doc-edit uses payload helper" grep -q 'mmw_payload_file_path' "$PLUGIN_DIR/hooks/guard-doc-edit.sh"
check "track-execution-state uses payload helper" grep -q 'mmw_payload_command' "$PLUGIN_DIR/hooks/track-execution-state.sh"

echo
echo "## Residue audit"
RUNTIME_SCAN_TARGETS=(
  "$PLUGIN_DIR/agents"
  "$PLUGIN_DIR/build"
  "$PLUGIN_DIR/hooks"
  "$PLUGIN_DIR/scripts"
  "$PLUGIN_DIR/skills"
  "$PLUGIN_DIR/state-schema"
  "$PLUGIN_DIR/architecture-draft.md"
  "$PLUGIN_DIR/hooks.json"
  "$PLUGIN_DIR/.codex-plugin/plugin.json"
)
OLD_HOST_UPPER="CLA""UDE"
OLD_HOST_TITLE="Cla""ude"
OLD_HOST_LOWER="cla""ude"
OLD_COMPANION="codex""-companion"
OLD_WORKER="codex""-worker"
OLD_EXEC="codex"" exec"
OLD_SCRIPT="CODEX""_SCRIPT"
OLD_SUBAGENT_FIELD="subagent""_type"
OLD_BACKGROUND_FIELD="run_in""_background"
OLD_MODEL_A="Op""us"
OLD_MODEL_B="Son""net"
OLD_TOOL_CALL="Agent""\\("
OLD_SKILL_CALL="Skill""\\(\\{ skill"
LEGACY_SEND_INPUT="send_input""\\(\\{[[:space:]]*to"
RESIDUE_PATTERN="${OLD_HOST_UPPER}_PLUGIN_ROOT|${OLD_HOST_UPPER}_CODE_EXPERIMENTAL|${OLD_HOST_TITLE}|${OLD_COMPANION}|${OLD_SCRIPT}|${OLD_WORKER}|${OLD_EXEC}|\\.${OLD_HOST_LOWER}|${OLD_SUBAGENT_FIELD}|${OLD_BACKGROUND_FIELD}|${OLD_TOOL_CALL}|${OLD_MODEL_A}|${OLD_MODEL_B}|${OLD_SKILL_CALL}|${LEGACY_SEND_INPUT}"
if rg -n --glob '!**/tests/**' --glob '!**/verify-maturity.sh' "$RESIDUE_PATTERN" "${RUNTIME_SCAN_TARGETS[@]}" >/tmp/mmw-codex-residue.$$ 2>/dev/null; then
  cat /tmp/mmw-codex-residue.$$
  rm -f /tmp/mmw-codex-residue.$$
  printf '  ✗ no foreign-host runtime residue\n'
  FAIL=$((FAIL + 1))
else
  rm -f /tmp/mmw-codex-residue.$$
  printf '  ✓ no foreign-host runtime residue\n'
  PASS=$((PASS + 1))
fi

echo
echo "## Active repo metadata"
check "marketplace override points at codex-orchestrate-new" grep -q 'codex-orchestrate-new/.codex-plugin/plugin.json' ".agents/plugins/agents.overrides.md"
check "marketplace source points at codex-orchestrate-new" jq -e '.plugins[] | select(.name == "multi-model-workflow") | .source.path == "./codex-orchestrate-new"' ".agents/plugins/marketplace.json"

echo
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
