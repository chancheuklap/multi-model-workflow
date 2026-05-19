#!/bin/bash
# PreToolUse hook for Bash tool.
# Cleans up orchestration temp files before git push / gh pr create.
# Runs AFTER guard-premature-push.sh — only reaches here if push is allowed.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

if ! echo "$COMMAND" | grep -qE 'git push|gh pr create'; then
  exit 0
fi

WORKFLOW_DIR=".claude/multi-model-workflow"
if [ ! -d "$WORKFLOW_DIR" ]; then
  exit 0
fi

CLEANED=()

if [ -f "$WORKFLOW_DIR/active-run-id" ]; then
  RUN_ID=$(cat "$WORKFLOW_DIR/active-run-id")

  for f in "$WORKFLOW_DIR/budget-"*.json "$WORKFLOW_DIR/scope-"*.md; do
    [ -f "$f" ] && rm -f "$f" && CLEANED+=("$(basename "$f")")
  done

  rm -f "$WORKFLOW_DIR/active-run-id" && CLEANED+=("active-run-id")
else
  for f in "$WORKFLOW_DIR/budget-"*.json "$WORKFLOW_DIR/scope-"*.md; do
    [ -f "$f" ] && rm -f "$f" && CLEANED+=("$(basename "$f")")
  done
fi

if [ ${#CLEANED[@]} -gt 0 ]; then
  echo "[multi-model-workflow] Cleaned up ${#CLEANED[@]} temp file(s): ${CLEANED[*]}" >&2
fi

exit 0
