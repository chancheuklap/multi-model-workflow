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
    /^[[:space:]]*-->/ { if (found) exit }
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
# repair_round 必须是非负整数,从源头收口:非数字("abc")会让下面的 [[ -ge ]] 在 set -u 下
# 把字符串当变量名而崩(rc=1 静默,且下游 dispatch-* 裸调用会被一起带崩);小数("1.5")会判
# false 而静默跳过 disposition_refs 必填校验(fail-open)。在此显式拒绝,得到干净的 exit 2。
if ! [[ "$REPAIR_ROUND" =~ ^[0-9]+$ ]]; then
  echo "Error: repair_round must be a non-negative integer, got '$REPAIR_ROUND'" >&2
  exit 2
fi
AGENT_ROLE=$(echo "$ENVELOPE_JSON" | jq -r '.agent_role')
REVIEW_INTENT=$(echo "$ENVELOPE_JSON" | jq -r '.review_intent // empty')
EXCEPTION_CODE=$(echo "$ENVELOPE_JSON" | jq -r '.exception_code // empty')
DISPOSITION_REFS=$(echo "$ENVELOPE_JSON" | jq -r '.disposition_refs // empty')

if [[ "$REPAIR_ROUND" -ge 1 ]]; then
  if [[ -z "$DISPOSITION_REFS" || "$DISPOSITION_REFS" == "null" || "$DISPOSITION_REFS" == "[]" ]]; then
    echo "Error: repair dispatch (round=$REPAIR_ROUND) must include non-empty disposition_refs" >&2
    exit 2
  fi
fi

if [[ "$AGENT_ROLE" == "codex_reviewer" ]]; then
  if [[ -z "$REVIEW_INTENT" || "$REVIEW_INTENT" == "null" ]]; then
    echo "Error: codex_reviewer dispatch must include review_intent" >&2
    exit 2
  fi
  case "$REVIEW_INTENT" in
    baseline|ad-hoc) ;;
    *)
      echo "Error: codex_reviewer review_intent must be baseline or ad-hoc" >&2
      exit 2
      ;;
  esac
fi

echo "$ENVELOPE_JSON"
