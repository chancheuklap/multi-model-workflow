#!/usr/bin/env bash
# Shim — delegates to dispatch-review.sh validate (D8 merge)
exec "$(dirname "$0")/dispatch-review.sh" validate "$@"
