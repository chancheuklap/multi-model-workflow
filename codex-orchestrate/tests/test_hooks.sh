#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

VALID_PROMPT="$TMP/valid-review.md"
INVALID_PROMPT="$TMP/invalid-review.md"

cat > "$VALID_PROMPT" <<'JSON'
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "hook-test",
  "phase": "execution",
  "agent_role": "reviewer",
  "agent_id": null,
  "pack_id": null,
  "repair_round": 0,
  "idempotency_key": "hook-test/review/r0",
  "disposition_refs": null,
  "review_intent": "baseline",
  "exception_code": null,
  "correlation_id": "hook-test/review"
}
-->
JSON

cat > "$INVALID_PROMPT" <<'JSON'
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "hook-test",
  "phase": "execution",
  "agent_role": "reviewer",
  "agent_id": null,
  "pack_id": null,
  "repair_round": 0,
  "idempotency_key": "hook-test/review/r0",
  "disposition_refs": null,
  "review_intent": null,
  "exception_code": null,
  "correlation_id": "hook-test/review"
}
-->
JSON

jq -n --arg cmd "bash $PLUGIN_DIR/scripts/review/review-lane.sh submit --lane codex --review-kind code --prompt-file $VALID_PROMPT --result-file $TMP/result.md" \
  '{tool_input:{command:$cmd}}' | bash "$PLUGIN_DIR/hooks/gate-external-review.sh"

if jq -n --arg cmd "bash $PLUGIN_DIR/scripts/review/review-lane.sh submit --lane codex --review-kind code --prompt-file $INVALID_PROMPT --result-file $TMP/result.md" \
  '{tool_input:{command:$cmd}}' | bash "$PLUGIN_DIR/hooks/gate-external-review.sh" 2>/dev/null; then
  echo "invalid review prompt was not blocked" >&2
  exit 1
fi

WORKDIR="$TMP/work"
mkdir -p "$WORKDIR"
if (
  cd "$WORKDIR"
  jq -n --arg path "docs/orchestrate/plans/demo.md" \
    '{tool_input:{file_path:$path}}' | bash "$PLUGIN_DIR/hooks/guard-doc-edit.sh"

  mkdir -p .codex/multi-model-workflow
  touch .codex/multi-model-workflow/worker-active
  jq -n --arg path "docs/orchestrate/plans/demo.md" \
    '{tool_input:{file_path:$path}}' | bash "$PLUGIN_DIR/hooks/guard-doc-edit.sh" 2>/dev/null
); then
  echo "worker-active doc edit was not blocked" >&2
  exit 1
fi
