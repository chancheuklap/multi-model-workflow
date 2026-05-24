#!/usr/bin/env bash
# PreToolUse hook for Bash (if: "Bash(git commit *)").
# Validates Pack commit message format. Uses workflow-state.
set -euo pipefail

INPUT=$(cat)
BUDGET_DIR=".codex/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [ ! -f "$SF" ]; then exit 0; fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
COMMIT_MSG=$(echo "$COMMAND" | sed -n 's/.*-m[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
if [ -z "$COMMIT_MSG" ]; then
  COMMIT_MSG=$(echo "$COMMAND" | sed -n "s/.*-m[[:space:]]*'\([^']*\)'.*/\1/p" | head -1)
fi

if [ -z "$COMMIT_MSG" ] || ! echo "$COMMIT_MSG" | grep -qiE '^Pack[[:space:]]'; then
  exit 0
fi

if ! echo "$COMMIT_MSG" | grep -qE '^Pack [0-9]+\.[0-9]+: .+'; then
  echo "[multi-model-workflow] BLOCKED: Pack commit message format invalid. Fix: use 'Pack N.M: <title> — <summary>'." >&2
  exit 2
fi

exit 0
