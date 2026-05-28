#!/usr/bin/env bash
# Pack 6.9: validate-multi-pr-dispatch.sh
#
# PreToolUse hook (Agent matcher) for multi-pr-merge phase dispatches.
# Fires when envelope.phase == "multi-pr-merge".
#
# 4 validation checks:
#   (a) merge-brief file exists at STATE_DIR/merge-brief-<run_id>.md
#   (b) META current_stage consistent with envelope.repair_round
#       (round=0 → stage must be in early stages; round≥1 → stage must be repair/integration_review+)
#   (c) if envelope contains conflict_id → §4 has that id AND status ≠ resolved
#   (d) dispatch prompt body contains string "merge-brief-<run_id>.md"
#       (prevents paste-content anti-pattern; if missing → agent would paste instead of referencing)
set -euo pipefail

INPUT=$(cat)
STATE_DIR="${STATE_DIR:-.claude/multi-model-workflow}"

# --- Parse prompt and extract DISPATCH_ENVELOPE directly ---
# We parse the envelope ourselves (not via parse-envelope.sh) because:
# - parse-envelope.sh validates disposition_refs for repair_round≥1, which doesn't
#   apply to multi-pr-merge repair rounds (they use conflict_id, not disposition_refs)
# - Early exit in parse-envelope.sh would suppress our validation checks

PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)
if [[ -z "$PROMPT" ]]; then exit 0; fi

# Try to extract the DISPATCH_ENVELOPE JSON block from the prompt (multi-line format)
ENVELOPE_JSON=$(echo "$PROMPT" | awk '
  /<!-- DISPATCH_ENVELOPE/ { found=1; next }
  /^-->/ { if (found) exit }
  found { printf "%s\n", $0 }
')

# Fall back to single-line format: <!-- DISPATCH_ENVELOPE {...} -->
if [[ -z "$ENVELOPE_JSON" ]]; then
  ENVELOPE_JSON=$(echo "$PROMPT" | sed -n 's/.*<!-- DISPATCH_ENVELOPE \(.*\) -->.*/\1/p' | head -1)
fi

# If no envelope found, not our responsibility — let other hooks handle it
if [[ -z "$ENVELOPE_JSON" ]] || ! echo "$ENVELOPE_JSON" | jq empty 2>/dev/null; then
  exit 0
fi

PHASE=$(echo "$ENVELOPE_JSON" | jq -r '.phase // empty')
# Only activate for multi-pr-merge phase
if [[ "$PHASE" != "multi-pr-merge" ]]; then
  exit 0
fi

RUN_ID=$(echo "$ENVELOPE_JSON" | jq -r '.run_id // empty')
if [[ -z "$RUN_ID" ]]; then
  echo "[multi-model-workflow] BLOCKED: envelope.run_id is missing for multi-pr-merge dispatch." >&2
  exit 2
fi

REPAIR_ROUND=$(echo "$ENVELOPE_JSON" | jq -r '.repair_round // 0')
CONFLICT_ID=$(echo "$ENVELOPE_JSON" | jq -r '.conflict_id // empty' 2>/dev/null || echo "")

MERGE_BRIEF_PATH="${STATE_DIR}/merge-brief-${RUN_ID}.md"

# --- Check (a): merge-brief file must exist ---
if [[ ! -f "$MERGE_BRIEF_PATH" ]]; then
  cat >&2 <<BLOCKED_MSG
[multi-model-workflow] BLOCKED: merge-brief not found for run_id=${RUN_ID}.

Expected path: ${MERGE_BRIEF_PATH}
Fix: run 'state.sh merge-brief init --run-id ${RUN_ID} --slug <slug>' then fill §2+§3 before dispatch.
BLOCKED_MSG
  exit 2
fi

# --- Check (b): META current_stage vs repair_round consistency ---
META_STAGE=$(python3 - "$MERGE_BRIEF_PATH" <<'PYEOF' 2>/dev/null || echo "ERROR"
import sys, re, json

filepath = sys.argv[1]
with open(filepath, 'r') as f:
    content = f.read()

m = re.search(r'<!--\s*MERGE_BRIEF_META\s*(.*?)\s*-->', content, re.DOTALL)
if not m:
    print('ERROR:no_meta_block')
    sys.exit(0)

try:
    meta = json.loads(m.group(1))
    print(meta.get('current_stage', 'ERROR:no_stage'))
except Exception:
    print('ERROR:invalid_meta_json')
PYEOF
)

if [[ "$META_STAGE" == ERROR* ]]; then
  cat >&2 <<BLOCKED_MSG
[multi-model-workflow] BLOCKED: merge-brief META block is missing or invalid.
Path: ${MERGE_BRIEF_PATH}
Fix: ensure the file has a valid <!-- MERGE_BRIEF_META { ... } --> block.
BLOCKED_MSG
  exit 2
fi

# Consistency rule:
# repair_round=0 → initial dispatch → stage should be init or conflict_discovery (not already in repair/complete)
# repair_round≥1 → subsequent dispatch → stage must NOT be init (merge-brief must have been progressed)
if [[ "$REPAIR_ROUND" -eq 0 ]]; then
  if [[ "$META_STAGE" == "complete" ]]; then
    cat >&2 <<BLOCKED_MSG
[multi-model-workflow] BLOCKED: repair_round=0 but merge-brief stage is '${META_STAGE}'.
This run appears already complete. Use a new run_id if starting a fresh merge.
BLOCKED_MSG
    exit 2
  fi
elif [[ "$REPAIR_ROUND" -ge 1 ]]; then
  if [[ "$META_STAGE" == "init" ]]; then
    cat >&2 <<BLOCKED_MSG
[multi-model-workflow] BLOCKED: repair_round=${REPAIR_ROUND} but merge-brief stage is 'init'.
Expected the merge-brief to be progressed past init before repair rounds.
Fix: run 'state.sh merge-brief stage --run-id ${RUN_ID} --stage conflict_discovery' (or later stage).
BLOCKED_MSG
    exit 2
  fi
fi

# --- Check (c): if conflict_id provided, it must exist in §4 with status ≠ resolved ---
if [[ -n "$CONFLICT_ID" ]]; then
  CONFLICT_CHECK=$(python3 - "$MERGE_BRIEF_PATH" "$CONFLICT_ID" <<'PYEOF' 2>/dev/null || echo "ERROR:check_failed"
import sys, re

filepath, conflict_id = sys.argv[1], sys.argv[2]
with open(filepath, 'r') as f:
    content = f.read()

def extract_section(text, start, end=None):
    i = text.find(start)
    if i == -1: return ''
    if end:
        j = text.find(end, i + len(start))
        return text[i:j] if j != -1 else text[i:]
    return text[i:]

section4 = extract_section(content, '## 4. Conflict', '## 5. Root Cause')

if conflict_id not in section4:
    print(f'ERROR:not_found:{conflict_id}')
    sys.exit(0)

# Find this specific conflict and check its status
pattern = rf'conflict_id[^:]*:\s*[`"]?{re.escape(conflict_id)}[`"]?'
m = re.search(pattern, section4)
if not m:
    print(f'ERROR:not_found:{conflict_id}')
    sys.exit(0)

snippet = section4[m.start():m.start()+500]
sm = re.search(r'\bstatus[^:]*:\s*[`"]?([^`"\n,]+)[`"]?', snippet)
if not sm:
    print(f'WARN:no_status:{conflict_id}')
    sys.exit(0)

status = sm.group(1).strip('` ')
if status == 'resolved':
    print(f'ERROR:already_resolved:{conflict_id}')
else:
    print(f'OK:{conflict_id}:{status}')
PYEOF
)

  if [[ "$CONFLICT_CHECK" == ERROR:not_found* ]]; then
    cat >&2 <<BLOCKED_MSG
[multi-model-workflow] BLOCKED: conflict_id '${CONFLICT_ID}' not found in §4 of merge-brief.
Path: ${MERGE_BRIEF_PATH}
Fix: ensure the conflict entry exists in §4 Conflict Findings before dispatching.
BLOCKED_MSG
    exit 2
  elif [[ "$CONFLICT_CHECK" == ERROR:already_resolved* ]]; then
    cat >&2 <<BLOCKED_MSG
[multi-model-workflow] BLOCKED: conflict_id '${CONFLICT_ID}' status=resolved — cannot dispatch repair for an already-resolved conflict.
Path: ${MERGE_BRIEF_PATH}
Fix: check if this conflict was already fixed; if a new issue arose, open a new conflict_id (C-NNN+1).
BLOCKED_MSG
    exit 2
  fi
fi

# --- Check (d): prompt body must contain "merge-brief-<run_id>.md" ---
EXPECTED_MERGE_BRIEF_REF="merge-brief-${RUN_ID}.md"
if ! echo "$PROMPT" | grep -qF "$EXPECTED_MERGE_BRIEF_REF"; then
  cat >&2 <<BLOCKED_MSG
[multi-model-workflow] BLOCKED: dispatch prompt for phase=multi-pr-merge does not reference merge-brief.

Expected string in prompt: "${EXPECTED_MERGE_BRIEF_REF}"
Missing reference = agent will paste content from memory instead of reading the merge-brief.

Fix: include the merge-brief path in the dispatch prompt:
  "Read \`.claude/multi-model-workflow/${EXPECTED_MERGE_BRIEF_REF}\` for PR list, contract map, and conflict details."
BLOCKED_MSG
  exit 2
fi

# All checks passed
exit 0
