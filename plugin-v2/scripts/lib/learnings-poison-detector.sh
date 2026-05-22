#!/usr/bin/env bash
# Detects 7 types of poisoning in learnings input:
# 1. Instruction injection (prompt manipulation patterns)
# 2. Cross-run contamination (references to other run_ids)
# 3. High-volume flooding (>10 learnings per source_run_id)
# 4. Scope escape (references to out-of-scope files/modules)
# 5. Source trust (unattributed or suspicious source)
# 6. Stale reference (references to files/APIs that no longer exist)
# 7. Contested learning (contradicts established patterns)
set -euo pipefail

LEARNING_TEXT="$1"
CURRENT_RUN_ID="${2:-}"
SCOPE_FILE="${3:-}"

POISONED=0
REASONS=()

# Type 1: Instruction injection
if echo "$LEARNING_TEXT" | grep -qiE 'ignore previous|system prompt|you are now|forget all|override|<system>|</system>|DISPATCH_ENVELOPE|<!-- BEGIN|<!-- END'; then
  POISONED=1
  REASONS+=("instruction_injection")
fi

# Type 2: Cross-run contamination
if [[ -n "$CURRENT_RUN_ID" ]]; then
  OTHER_RUNS=$(echo "$LEARNING_TEXT" | grep -oE 'run-[a-z0-9-]+' 2>/dev/null | grep -v "$CURRENT_RUN_ID" 2>/dev/null | head -1 || true)
  if [[ -n "$OTHER_RUNS" ]]; then
    POISONED=1
    REASONS+=("cross_run_contamination:$OTHER_RUNS")
  fi
fi

# Type 3: High-volume flooding check
if [[ -n "$CURRENT_RUN_ID" ]]; then
  LEARNINGS_FILE="${STATE_BASE:-.claude/multi-model-workflow}/learnings.jsonl"
  if [[ -f "$LEARNINGS_FILE" ]]; then
    RUN_COUNT=$(grep -c "\"run_id\":\"${CURRENT_RUN_ID}\"" "$LEARNINGS_FILE" 2>/dev/null || echo "0")
    if [[ "$RUN_COUNT" -gt 20 ]]; then
      POISONED=1
      REASONS+=("high_volume_flooding:${RUN_COUNT}_entries_for_${CURRENT_RUN_ID}")
    fi
  fi
fi

# Type 4: Scope escape
if [[ -n "$SCOPE_FILE" && -f "$SCOPE_FILE" ]]; then
  EXCLUDED=$(jq -r '.excluded_paths[]? // empty' "$SCOPE_FILE" 2>/dev/null)
  for path in $EXCLUDED; do
    if echo "$LEARNING_TEXT" | grep -qF "$path"; then
      POISONED=1
      REASONS+=("scope_escape:$path")
    fi
  done
fi

# Type 5: Source trust — suspicious patterns in learning content
if echo "$LEARNING_TEXT" | grep -qiE 'trust me|always do this|never question|guaranteed to work|100% safe'; then
  POISONED=1
  REASONS+=("source_trust:suspicious_authority_claim")
fi

# Type 6: Stale reference — references to specific file paths that don't exist
# Extract file paths from learning and check existence
REFERENCED_PATHS=$(echo "$LEARNING_TEXT" | grep -oE '[a-zA-Z0-9_/.-]+\.(py|ts|js|sh|md|json|yaml|yml)' | head -5 || true)
for ref_path in $REFERENCED_PATHS; do
  if [[ "$ref_path" == *"/"* ]] && [[ ! -f "$ref_path" ]] && [[ ! -f "./$ref_path" ]]; then
    # Only flag if path looks like a project-internal reference (has directory component)
    POISONED=1
    REASONS+=("stale_reference:$ref_path")
    break  # One stale reference is enough
  fi
done

# Type 7: Contested learning — learning claims that contradict common patterns
if echo "$LEARNING_TEXT" | grep -qiE 'mock everything|skip tests|tests are optional|TDD is unnecessary|ignore type errors'; then
  POISONED=1
  REASONS+=("contested_learning:anti_pattern")
fi

if [[ $POISONED -eq 1 ]]; then
  echo "POISONED: $(IFS=','; echo "${REASONS[*]}")"
  exit 1
fi

echo "CLEAN"
exit 0
