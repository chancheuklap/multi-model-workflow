#!/usr/bin/env bash
# Compatibility entrypoint for the Codex Review gate.
# The active Codex-native implementation is gate-external-review.sh, which
# validates review-lane.sh submit commands and their DISPATCH_ENVELOPE.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec bash "$SCRIPT_DIR/gate-external-review.sh"
