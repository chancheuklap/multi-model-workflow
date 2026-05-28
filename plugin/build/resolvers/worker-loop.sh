#!/usr/bin/env bash
# Resolver for the <!-- BEGIN: worker-loop --> anchor.
# Injects worker-loop.md.tmpl content into pack-executor.md and complex-pack-executor.md.
# Plan 005 Pack 5.1.
set -euo pipefail

TEMPLATE_DIR="$1"
ANCHOR_NAME="$2"
VARIANT="${3:-}"  # not currently used; reserved for future per-agent variants

TEMPLATE_FILE="$TEMPLATE_DIR/${ANCHOR_NAME}.md.tmpl"

if [[ ! -f "$TEMPLATE_FILE" ]]; then
  echo "Error: template not found: $TEMPLATE_FILE" >&2
  exit 1
fi

cat "$TEMPLATE_FILE"
