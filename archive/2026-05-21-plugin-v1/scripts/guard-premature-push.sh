#!/bin/bash
# Blocks git push/merge/PR creation if unchecked tasks remain in the active plan.
# Used as a PreToolUse hook for the Bash tool.

if ! command -v jq >/dev/null 2>&1; then
  echo "[multi-model-workflow] jq not found — guard-premature-push requires jq. Skipping." >&2
  exit 0
fi

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if ! echo "$COMMAND" | grep -qE 'git push|git merge|gh pr create'; then
  exit 0
fi

PLAN=$(ls -t docs/orchestrate/plans/*.md 2>/dev/null | head -1)
if [ -z "$PLAN" ]; then
  exit 0
fi

UNCHECKED=$(grep -c '^\s*- \[ \]' "$PLAN" 2>/dev/null)
if [ "${UNCHECKED:-0}" -gt 0 ]; then
  echo "Plan has ${UNCHECKED} unchecked tasks. Complete execution and review before pushing." >&2
  exit 2
fi

exit 0
