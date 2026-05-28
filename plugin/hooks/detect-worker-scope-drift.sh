#!/usr/bin/env bash
# Plan 005 Pack 5.19: detect-worker-scope-drift.sh
#
# PostToolUse hook for Edit + Write tools.
# In Plan-level autonomous mode the Worker commits 5+ packs without Coordinator
# touch points. This hook tracks scope drift WITHOUT blocking — Worker keeps
# going, but every drift Edit is recorded so Coordinator sees it at Plan boundary.
#
# Trigger: PostToolUse Edit/Write, worker-active marker present.
# Behavior:
#   1. Resolve current plan from worker-active marker (Coordinator writes plan_id).
#   2. Parse plan.md "Owned files" sections per pack → union of all owned_files.
#   3. If hook input file_path:
#        - inside current pack's owned_files → silent allow.
#        - inside same plan's other pack owned_files → drift_note (allow).
#        - outside the plan's owned_files entirely → WARN + append to
#          execution-state.plans[N].drift_warnings[].
#   4. Never BLOCK — only record (Coordinator inspects at Plan boundary).
set -euo pipefail

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[[ -z "$FILE_PATH" ]] && exit 0

BUDGET_DIR=".claude/multi-model-workflow"
WORKER_MARKER="${BUDGET_DIR}/worker-active"

# Only fire when worker session is active
[[ ! -f "$WORKER_MARKER" ]] && exit 0

# Resolve current run + plan
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
[[ ! -f "$RUN_ID_FILE" ]] && exit 0
RUN_ID=$(cat "$RUN_ID_FILE")

# worker-active file optionally contains plan_id (first line) for routing
PLAN_ID=""
if [[ -s "$WORKER_MARKER" ]]; then
  PLAN_ID=$(head -1 "$WORKER_MARKER" 2>/dev/null || echo "")
fi

ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
[[ ! -f "$ESF" ]] && exit 0

# Fall back: derive plan_id from execution-state where worker_agent_id is set
if [[ -z "$PLAN_ID" ]]; then
  PLAN_ID=$(jq -r '[.plans | to_entries[] | select(.value.worker_agent_id != null and .value.worker_agent_id != "") | .key] | first // empty' "$ESF" 2>/dev/null || echo "")
fi

[[ -z "$PLAN_ID" ]] && exit 0

# Read plan.md for the plan owned_files union
PLAN_PATH=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].plan_path // empty' "$ESF" 2>/dev/null || echo "")
# Fallback: search docs/orchestrate/plans for matching ID
if [[ -z "$PLAN_PATH" ]] || [[ ! -f "$PLAN_PATH" ]]; then
  PLAN_PATH=$(find docs/orchestrate/plans -name "${PLAN_ID}-*.md" -type f 2>/dev/null | head -1)
fi
[[ -z "$PLAN_PATH" || ! -f "$PLAN_PATH" ]] && exit 0

# Parse owned_files: lines like `- Edit: path/to/file` or `- Create: path` under
# `### Owned files` sections. Use sed/python for portability (macOS awk does not
# support GNU's match-with-array extension).
OWNED_FILES=$(python3 - "$PLAN_PATH" <<'PYEOF'
import re
import sys

path = sys.argv[1]
with open(path) as f:
    lines = f.readlines()

in_section = False
results = []
verb_re = re.compile(r'^- (?:Edit|Create|Delete|Rewrite|Edit/Create): (.+?)\s*$')
plain_re = re.compile(r'^- ([^ ].+\.[a-zA-Z]+)\s*$')

for line in lines:
    line = line.rstrip('\n')
    if line.startswith('### Owned files'):
        in_section = True
        continue
    if line.startswith('### ') or line.startswith('## '):
        in_section = False
        continue
    if in_section:
        m = verb_re.match(line)
        if m:
            results.append(m.group(1).strip())
            continue
        m = plain_re.match(line)
        if m:
            results.append(m.group(1).strip())

for r in results:
    print(r)
PYEOF
)

# Normalize FILE_PATH to repository-relative (strip leading workspace)
REL_PATH="$FILE_PATH"
REPO_ROOT=$(pwd)
if [[ "$REL_PATH" == "$REPO_ROOT"/* ]]; then
  REL_PATH="${REL_PATH#$REPO_ROOT/}"
fi

# Check if REL_PATH appears in OWNED_FILES (substring of any line)
IN_SCOPE="false"
while IFS= read -r owned; do
  [[ -z "$owned" ]] && continue
  # Match exact match or wildcard suffix
  if [[ "$REL_PATH" == "$owned" ]] || [[ "$REL_PATH" == */"$owned" ]] || [[ "$owned" == *"$REL_PATH" ]]; then
    IN_SCOPE="true"
    break
  fi
done <<< "$OWNED_FILES"

if [[ "$IN_SCOPE" == "true" ]]; then
  exit 0
fi

# Drift detected — log to execution-state without blocking
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../scripts/lib/state-lock.sh"
LOCK_DIR="${BUDGET_DIR}/${RUN_ID}.lock"
state_lock_acquire "$LOCK_DIR"
trap 'state_lock_release "$LOCK_DIR"' EXIT

NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
jq --arg pid "$PLAN_ID" --arg fp "$REL_PATH" --arg ts "$NOW" '
  .plans[$pid].drift_warnings = ((.plans[$pid].drift_warnings // []) + [{file_path: $fp, recorded_at: $ts}])
' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"

jq -n --arg msg "[multi-model-workflow] WARN: scope drift — Worker edited '$REL_PATH' not in plan $PLAN_ID owned_files. Recorded for Coordinator review at Plan boundary. Continuing." \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'

exit 0
