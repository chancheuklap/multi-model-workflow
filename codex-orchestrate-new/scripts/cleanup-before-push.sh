#!/usr/bin/env bash
# PostToolUse hook for Bash tool (if: "Bash(git push *)").
# Cleans up orchestration temp files AFTER a successful push.
#
# Also callable directly: cleanup-before-push.sh --force
# Used by Closing after hotfix post-push review completes.

FORCE=false
if [ "${1:-}" = "--force" ]; then
  FORCE=true
fi

if [ "$FORCE" = false ]; then
  INPUT=$(cat)

  EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0' 2>/dev/null)
  if [ "$EXIT_CODE" != "0" ]; then exit 0; fi

  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

  if ! echo "$COMMAND" | grep -qE 'git push|gh pr create'; then
    exit 0
  fi
fi

WORKFLOW_DIR=".codex/multi-model-workflow"

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

# Hotfix sub-mode: defer cleanup — post-push review still needs state files.
# Closing calls this script with --force after post-push review completes.
#
# Judgement is the live commit_format flag, not the dead route=="hotfix" check
# (route enum has no "hotfix" value — hotfix is a formal sub-mode marked via
# commit_format_override="hotfix-unreviewed"). We read the per-run state flag
# first (commit_format / commit_format_override), then fall back to the route's
# manifest commit_format. Fail-open: if no hotfix marker is found, cleanup runs.
if [ "$FORCE" = false ]; then
  RUN_ID_FILE="${WORKFLOW_DIR}/active-run-id"
  if [ -f "$RUN_ID_FILE" ]; then
    RUN_ID=$(cat "$RUN_ID_FILE" 2>/dev/null)
    STATE_FILE="${WORKFLOW_DIR}/workflow-state-${RUN_ID}.json"
    if [ -f "$STATE_FILE" ] && command -v jq >/dev/null 2>&1; then
      COMMIT_FORMAT=$(jq -r '.commit_format // .commit_format_override // empty' "$STATE_FILE" 2>/dev/null)
      if [ -z "$COMMIT_FORMAT" ]; then
        # Fall back to the route's declared commit_format in routes-v1.json.
        ROUTE=$(jq -r '.route // empty' "$STATE_FILE" 2>/dev/null)
        ROUTES_MANIFEST="$(cd "$(dirname "$0")" && pwd)/../state-schema/routes-v1.json"
        if [ -n "$ROUTE" ] && [ -f "$ROUTES_MANIFEST" ]; then
          COMMIT_FORMAT=$(jq -r --arg r "$ROUTE" '.routes[$r].commit_format // empty' "$ROUTES_MANIFEST" 2>/dev/null)
        fi
      fi
      if [ "$COMMIT_FORMAT" = "hotfix-unreviewed" ]; then
        echo "[multi-model-workflow] Hotfix sub-mode: deferring cleanup until post-push review completes." >&2
        exit 0
      fi
    fi
  fi
fi

COUNT=$(find "$WORKFLOW_DIR" -mindepth 1 -print | wc -l | tr -d ' ')

if [ "$COUNT" -eq 0 ]; then
  exit 0
fi

rm -rf "$WORKFLOW_DIR"
echo "[multi-model-workflow] Cleaned up $COUNT runtime state file(s) under $WORKFLOW_DIR" >&2

exit 0
