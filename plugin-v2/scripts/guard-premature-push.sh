#!/bin/bash
# PreToolUse hook for Bash tool.
# Two responsibilities:
# 1. Block git push / gh pr create if unchecked tasks remain in the active plan.
# 2. Block git merge --squash and git rebase — merge strategy rule enforcement.

if ! command -v jq >/dev/null 2>&1; then
  echo "[multi-model-workflow] jq not found — guard-premature-push requires jq. Skipping." >&2
  exit 0
fi

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# --- Rule 1: Merge strategy enforcement (always active, no plan check needed) ---

if echo "$COMMAND" | grep -qE 'git merge\b.*--squash'; then
  echo "[multi-model-workflow] BLOCKED: git merge --squash is forbidden. Use git merge --no-ff to preserve commit history." >&2
  exit 2
fi

if echo "$COMMAND" | grep -qE 'git rebase\b'; then
  echo "[multi-model-workflow] BLOCKED: git rebase is forbidden. Use git merge --no-ff to preserve commit history." >&2
  exit 2
fi

# --- Rule 2: Block premature push/PR when plan has unchecked tasks ---

if ! echo "$COMMAND" | grep -qE 'git push|gh pr create'; then
  exit 0
fi

UNCHECKED=$(find docs/orchestrate/plans -name '*.md' -exec grep -c '^\s*- \[ \]' {} + 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
if [ "${UNCHECKED}" -gt 0 ]; then
  echo "[multi-model-workflow] BLOCKED: Plans have ${UNCHECKED} unchecked tasks. Complete execution and review before pushing." >&2
  exit 2
fi

exit 0
