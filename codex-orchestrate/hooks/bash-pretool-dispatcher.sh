#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

run_guard() {
  local script="$1"
  printf '%s' "$INPUT" | bash "$script"
}

run_guard "$SCRIPT_DIR/../scripts/guard-premature-push.sh"
run_guard "$SCRIPT_DIR/enforce-pack-commit.sh"
run_guard "$SCRIPT_DIR/gate-external-review.sh"
run_guard "$SCRIPT_DIR/validate-dispatch-command.sh"

exit 0
