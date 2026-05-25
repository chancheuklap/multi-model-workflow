#!/usr/bin/env bash
set -euo pipefail

TEMPLATE_DIR="$1"
anchor="${2:-repair-routing}"
variant="${3:-default}"

if [[ "$anchor" != "repair-routing" ]]; then
  exit 1
fi

cat "$TEMPLATE_DIR/repair-routing.md.tmpl"
