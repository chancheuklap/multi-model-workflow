#!/usr/bin/env bash
# PreToolUse hook for Bash (if: "Bash(git commit *)").
# Validates Pack commit message format BEFORE the commit executes.
# Pack commits must follow: "Pack N.M: <title> — <summary>"
# Non-Pack commits are silently passed through.
set -euo pipefail

INPUT=$(cat)
BUDGET_DIR=".claude/multi-model-workflow"
if [ ! -f "${BUDGET_DIR}/active-run-id" ]; then exit 0; fi
if [ ! -f "${BUDGET_DIR}/execution-state-$(cat "${BUDGET_DIR}/active-run-id").json" ]; then exit 0; fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
COMMIT_MSG=$(echo "$COMMAND" | sed -n 's/.*-m[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
if [ -z "$COMMIT_MSG" ]; then
  COMMIT_MSG=$(echo "$COMMAND" | sed -n "s/.*-m[[:space:]]*'\([^']*\)'.*/\1/p" | head -1)
fi

# Non-Pack commit (design/plan repair, merge, etc.) → pass through
if [ -z "$COMMIT_MSG" ] || ! echo "$COMMIT_MSG" | grep -qiE '^Pack[[:space:]]'; then
  exit 0
fi

# Pack commit → format must match "Pack N.M: ..."
if ! echo "$COMMIT_MSG" | grep -qE '^Pack [0-9]+\.[0-9]+: .+'; then
  echo "[multi-model-workflow] BLOCKED: Pack commit message format invalid. Fix: use 'Pack N.M: <title> — <summary>'." >&2
  exit 2
fi

exit 0
