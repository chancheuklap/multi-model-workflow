#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

printf '%s' "$INPUT" | bash "$SCRIPT_DIR/guard-doc-edit.sh"

exit 0
