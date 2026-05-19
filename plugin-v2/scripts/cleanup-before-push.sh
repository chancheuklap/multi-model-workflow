#!/usr/bin/env bash
# PreToolUse hook for Bash tool.
# Cleans up orchestration temp files before git push / gh pr create.
# Runs AFTER guard-premature-push.sh — only reaches here if push is allowed.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

if ! echo "$COMMAND" | grep -qE 'git push|gh pr create'; then
  exit 0
fi

WORKFLOW_DIR=".claude/multi-model-workflow"

if [ ! -e "$WORKFLOW_DIR" ]; then
  exit 0
fi

if [ -L "$WORKFLOW_DIR" ]; then
  echo "[multi-model-workflow] WARNING: refusing to clean symlinked state directory: $WORKFLOW_DIR" >&2
  exit 0
fi

if [ ! -d "$WORKFLOW_DIR" ]; then
  echo "[multi-model-workflow] WARNING: state path is not a directory: $WORKFLOW_DIR" >&2
  exit 0
fi

COUNT=$(find "$WORKFLOW_DIR" -mindepth 1 -print | wc -l | tr -d ' ')

if [ "$COUNT" -eq 0 ]; then
  exit 0
fi

rm -rf "$WORKFLOW_DIR"
echo "[multi-model-workflow] Cleaned up $COUNT runtime state file(s) under $WORKFLOW_DIR" >&2

exit 0
