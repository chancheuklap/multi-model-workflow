#!/usr/bin/env bash
# Detects 4 types of poisoning in learnings input:
# 1. Instruction injection (prompt manipulation patterns)
# 2. Cross-run contamination (references to other run_ids)
# 3. High-volume flooding (>10 learnings per source_run_id)
# 4. Scope escape (references to out-of-scope files/modules)
set -euo pipefail

LEARNING_TEXT="$1"
CURRENT_RUN_ID="${2:-}"
SCOPE_FILE="${3:-}"

POISONED=0
REASONS=()

# Type 1: Instruction injection
if echo "$LEARNING_TEXT" | grep -qiE 'ignore previous|system prompt|you are now|forget all|override|<system>|</system>'; then
  POISONED=1
  REASONS+=("instruction_injection")
fi

# Type 2: Cross-run contamination
if [[ -n "$CURRENT_RUN_ID" ]]; then
  OTHER_RUNS=$(echo "$LEARNING_TEXT" | grep -oE 'run-[a-z0-9-]+' | grep -v "$CURRENT_RUN_ID" | head -1)
  if [[ -n "$OTHER_RUNS" ]]; then
    POISONED=1
    REASONS+=("cross_run_contamination:$OTHER_RUNS")
  fi
fi

# Type 3: High-volume check (caller must provide count)
# Handled externally by learnings-jsonl.sh

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

if [[ $POISONED -eq 1 ]]; then
  echo "POISONED: $(IFS=','; echo "${REASONS[*]}")"
  exit 1
fi

echo "CLEAN"
exit 0
