#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

run_hook() {
  local script="$1"
  printf '%s' "$INPUT" | bash "$script"
}

run_hook "$SCRIPT_DIR/track-review-budget.sh"
run_hook "$SCRIPT_DIR/track-execution-state.sh"
run_hook "$SCRIPT_DIR/../scripts/cleanup-before-push.sh"

exit 0
