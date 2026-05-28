#!/usr/bin/env bash
# Plan 005 Pack 5.18: guard-plan-doc-patch.sh
#
# PreToolUse hook for Write tool, matching paths ending in `doc-patch.diff`.
# Validates that Worker-written doc-patch content only touches plan-document
# acceptance checkbox lines (`^- \[[ x]\]`). This is a defensive backstop —
# the Worker is supposed to follow Decision 6's restriction, but a buggy
# Worker could in principle smuggle arbitrary doc edits through a doc-patch.
#
# Rules (must ALL hold for every patch hunk):
#   1. Diff target paths are docs/orchestrate/plans/<slug>/<file>.md (plan docs)
#   2. Every +/- (non-context) line is a Markdown checkbox: `^- \[[ x]\] ` ...
#   3. The change is a checkbox toggle (`- [ ]` ↔ `- [x]`) — the text after the
#      checkbox marker matches between minus and plus sides.
#
# Violations → BLOCKED exit 2 with line-level explanation.
set -euo pipefail

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty' 2>/dev/null)

[[ -z "$FILE_PATH" ]] && exit 0

# Only intercept doc-patch.diff files (Worker artifact path convention)
if [[ "$FILE_PATH" != *doc-patch.diff ]]; then
  exit 0
fi

# Empty patch is a no-op — allow
[[ -z "$CONTENT" ]] && exit 0

# Walk the diff. Validate:
#   - Target file paths under docs/orchestrate/plans/.../*.md only
#   - Every "+" or "-" line (excluding "+++ /---") matches checkbox shape
#   - Paired "-" then "+" toggle the checkbox state and keep text identical
#
# Implementation: a small Python parser is simpler than awk here.
RESULT=$(python3 - "$CONTENT" <<'PYEOF'
import re
import sys

patch = sys.argv[1]
lines = patch.split("\n")

errors = []
current_target = None
i = 0
n = len(lines)

# Track the most recent "-" and "+" within a hunk to validate toggles pair-by-pair
def is_checkbox(line_body):
    # body without the leading +/- prefix
    return re.match(r'^- \[[ x]\] ', line_body) is not None

def checkbox_text(line_body):
    # extract the text after "- [x] " or "- [ ] "
    m = re.match(r'^- \[[ x]\] (.*)$', line_body)
    return m.group(1) if m else None

while i < n:
    line = lines[i]
    if line.startswith("--- ") or line.startswith("+++ "):
        # path lines — capture target (b/ path)
        if line.startswith("+++ "):
            p = line[4:].strip()
            # strip "b/" prefix if present
            if p.startswith("b/"):
                p = p[2:]
            current_target = p
            if not re.match(r'^docs/orchestrate/plans/[^/]+/[^/]+\.md$', p):
                errors.append(f"target file not a plan doc: {p}")
        i += 1
        continue
    if line.startswith("diff ") or line.startswith("index ") or line.startswith("@@"):
        i += 1
        continue
    if line.startswith("+") or line.startswith("-"):
        # body change line
        body = line[1:]  # strip prefix
        if not is_checkbox(body):
            errors.append(f"non-checkbox change line: {line[:120]}")
    i += 1

# Pair toggles: walk again and collect consecutive -/+ pairs in each hunk,
# verify text portion matches
i = 0
while i < n:
    line = lines[i]
    if line.startswith("-") and not line.startswith("--- "):
        body_minus = line[1:]
        if i + 1 < n and lines[i+1].startswith("+") and not lines[i+1].startswith("+++ "):
            body_plus = lines[i+1][1:]
            tm = checkbox_text(body_minus)
            tp = checkbox_text(body_plus)
            if tm is None or tp is None:
                # Already flagged above
                pass
            elif tm != tp:
                errors.append(f"checkbox text changed (not a pure toggle): '{tm}' → '{tp}'")
            i += 2
            continue
    i += 1

if errors:
    print("BLOCK")
    for e in errors:
        print(e)
else:
    print("OK")
PYEOF
)

if echo "$RESULT" | head -1 | grep -q "^BLOCK"; then
  REASONS=$(echo "$RESULT" | tail -n +2)
  echo "[multi-model-workflow] BLOCKED: doc-patch.diff content violates plan-checkbox-only rule (Decision 6 / Pack 5.18 guard):" >&2
  echo "$REASONS" >&2
  exit 2
fi

exit 0
