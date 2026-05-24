#!/usr/bin/env bash
# PreToolUse hook for Edit and Write tools.
# Blocks worker agents from modifying design docs and plan docs.
#
# Detection: Coordinator creates .codex/multi-model-workflow/worker-active
# before dispatching a worker and removes it after the worker returns.
# If worker-active exists → worker context → block docs/ modifications.
#
# Protected paths: docs/ directory (design docs, plan docs, reviews)
set -euo pipefail

INPUT=$(cat)

# Extract file_path from tool_input (works for Edit, Write, and apply_patch-like payloads)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[[ -z "$FILE_PATH" ]] && exit 0

# Only guard docs/ paths
if ! echo "$FILE_PATH" | grep -qE '(^|/)docs/'; then
  exit 0
fi

# No workflow state directory at all → no active workflow → allow
WORKFLOW_DIR=".codex/multi-model-workflow"
if [[ ! -d "$WORKFLOW_DIR" ]]; then
  exit 0
fi

# Worker context: worker-active marker exists → block
WORKER_MARKER="${WORKFLOW_DIR}/worker-active"
if [[ -f "$WORKER_MARKER" ]]; then
  echo "[multi-model-workflow] BLOCKED: Worker agents (pack_executor, complex_pack_executor) cannot modify design or plan documents under docs/. Only the Coordinator may edit these files." >&2
  exit 2
fi

# Coordinator context (no worker-active marker) → allow
exit 0
