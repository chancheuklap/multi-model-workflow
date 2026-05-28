#!/usr/bin/env bash
# Shared envelope parser for all hooks.
# Input: prompt text (from stdin or $1 as file path)
# Output: parsed JSON to stdout
# Exit 2 on missing/malformed envelope or failed conditional validation.
set -euo pipefail

if [[ $# -ge 1 && -f "$1" ]]; then
  PROMPT_TEXT=$(cat "$1")
else
  PROMPT_TEXT=$(cat)
fi

# Try single-line format: <!-- DISPATCH_ENVELOPE {...} -->
ENVELOPE_JSON=$(echo "$PROMPT_TEXT" | sed -n 's/.*<!-- DISPATCH_ENVELOPE \(.*\) -->.*/\1/p' | head -1)

# Fall back to multi-line format:
# <!-- DISPATCH_ENVELOPE
# { ... }
# -->
if [[ -z "$ENVELOPE_JSON" ]]; then
  ENVELOPE_JSON=$(echo "$PROMPT_TEXT" | awk '
    /<!-- DISPATCH_ENVELOPE/ { found=1; next }
    /^-->/ { if (found) exit }
    found { printf "%s", $0 }
  ')
fi

if [[ -z "$ENVELOPE_JSON" ]]; then
  echo "Error: DISPATCH_ENVELOPE not found in prompt" >&2
  exit 2
fi

if ! echo "$ENVELOPE_JSON" | jq empty 2>/dev/null; then
  echo "Error: DISPATCH_ENVELOPE is not valid JSON" >&2
  exit 2
fi

for field in protocol_version run_id phase agent_role repair_round idempotency_key; do
  val=$(echo "$ENVELOPE_JSON" | jq -r ".$field // empty")
  if [[ -z "$val" ]]; then
    echo "Error: missing required field: $field" >&2
    exit 2
  fi
done

REPAIR_ROUND=$(echo "$ENVELOPE_JSON" | jq -r '.repair_round')
AGENT_ROLE=$(echo "$ENVELOPE_JSON" | jq -r '.agent_role')
REVIEW_INTENT=$(echo "$ENVELOPE_JSON" | jq -r '.review_intent // empty')
EXCEPTION_CODE=$(echo "$ENVELOPE_JSON" | jq -r '.exception_code // empty')
DISPOSITION_REFS=$(echo "$ENVELOPE_JSON" | jq -r '.disposition_refs // empty')

if [[ "$REPAIR_ROUND" -ge 1 ]] 2>/dev/null; then
  if [[ -z "$DISPOSITION_REFS" || "$DISPOSITION_REFS" == "null" || "$DISPOSITION_REFS" == "[]" ]]; then
    echo "Error: repair dispatch (round=$REPAIR_ROUND) must include non-empty disposition_refs" >&2
    exit 2
  fi
fi

if [[ "$AGENT_ROLE" == "codex-reviewer" ]]; then
  if [[ -z "$REVIEW_INTENT" || "$REVIEW_INTENT" == "null" ]]; then
    echo "Error: codex-reviewer dispatch must include review_intent" >&2
    exit 2
  fi
  case "$REVIEW_INTENT" in
    baseline) ;;
    *)
      echo "Error: codex-reviewer review_intent must be baseline" >&2
      exit 2
      ;;
  esac
fi

echo "$ENVELOPE_JSON"
