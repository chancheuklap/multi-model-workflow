#!/usr/bin/env bash
# PreToolUse hook for Edit and Write tools.
# Blocks worker agents from modifying design docs and plan docs.
#
# Detection: Workers dispatched with isolation: "worktree" get a clean worktree
# without .claude/ (gitignored). The Coordinator's working directory has
# .claude/multi-model-workflow/active-run-id (created during infrastructure setup).
# If active-run-id is absent → worker context → block docs/ modifications.
#
# Protected paths: docs/ directory (design docs, plan docs, reviews)
set -euo pipefail

INPUT=$(cat)

# Extract file_path from tool_input (works for both Edit and Write)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[[ -z "$FILE_PATH" ]] && exit 0

# Only guard docs/ paths
if ! echo "$FILE_PATH" | grep -qE '(^|/)docs/'; then
  exit 0
fi

# No workflow state directory at all → no active workflow → allow
WORKFLOW_DIR=".claude/multi-model-workflow"
if [[ ! -d "$WORKFLOW_DIR" ]]; then
  exit 0
fi

# Coordinator context: active-run-id exists → allow
ACTIVE_RUN_FILE="${WORKFLOW_DIR}/active-run-id"
if [[ -f "$ACTIVE_RUN_FILE" ]]; then
  exit 0
fi

# Worker context (workflow dir exists but no active-run-id) → block
echo "[multi-model-workflow] BLOCKED: Worker agents (pack-executor, complex-pack-executor) cannot modify design or plan documents under docs/. Only the Coordinator may edit these files." >&2
exit 2
