#!/usr/bin/env bash
set -euo pipefail

TEMPLATE_DIR="$1"
ANCHOR_NAME="$2"
VARIANT="${3:-}"

TEMPLATE_FILE="$TEMPLATE_DIR/${ANCHOR_NAME}.md.tmpl"

if [[ ! -f "$TEMPLATE_FILE" ]]; then
  echo "Error: template not found: $TEMPLATE_FILE" >&2
  exit 1
fi

cat "$TEMPLATE_FILE"
