#!/usr/bin/env bash
set -euo pipefail

TEMPLATE_DIR="$1"
ANCHOR_NAME="$2"
VARIANT="${3:-}"

TEMPLATE_FILE="$TEMPLATE_DIR/preamble.md.tmpl"

if [[ ! -f "$TEMPLATE_FILE" ]]; then
  echo "Error: preamble template not found: $TEMPLATE_FILE" >&2
  exit 1
fi

if [[ -n "$VARIANT" ]]; then
  # Extract [variant=X]...[/variant] block from the template
  sed -n "/\[variant=$VARIANT\]/,/\[\/variant\]/{ /\[variant=/d; /\[\/variant\]/d; p; }" "$TEMPLATE_FILE"
else
  cat "$TEMPLATE_FILE"
fi
