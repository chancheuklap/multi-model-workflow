#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
COMMAND="$(printf '%s' "$INPUT" | jq -r 'if type == "object" then (.tool_input.command // empty) else empty end' 2>/dev/null || true)"
[[ -z "$COMMAND" ]] && exit 0

if ! echo "$COMMAND" | grep -qE 'scripts/dispatch/(dispatch-gateway|worktree-exec|worktree-resume)\.sh'; then
  exit 0
fi

if echo "$COMMAND" | grep -q 'scripts/dispatch/worktree-resume\.sh'; then
  if ! echo "$COMMAND" | grep -q -- '--job-file'; then
    echo "[codex-orchestrate] BLOCKED: worktree-resume command must include --job-file." >&2
    exit 2
  fi
  if ! echo "$COMMAND" | grep -q -- '--repair-prompt'; then
    echo "[codex-orchestrate] BLOCKED: worktree-resume command must include --repair-prompt." >&2
    exit 2
  fi
  exit 0
fi

if ! echo "$COMMAND" | grep -q -- '--envelope-file'; then
  echo "[codex-orchestrate] BLOCKED: dispatch command must include --envelope-file." >&2
  exit 2
fi

exit 0
