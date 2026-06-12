#!/usr/bin/env bash
# Codex PostToolUse hook placeholder for review budget.
#
# Codex review dispatch is owned by explicit scripts:
#   dispatch-review.sh validate
#   dispatch-review.sh record
#   complete-review-dispatch.sh
#
# The budget is incremented exactly once by complete-review-dispatch.sh when the
# Coordinator persists a reviewer result file. This hook intentionally does not
# infer review completion from shell command text, because Codex reviews are
# native subagents, not external companion jobs.
set -euo pipefail
exit 0
