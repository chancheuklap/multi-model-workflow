#!/usr/bin/env bash
# Shim — delegates to dispatch-route-worker.sh record (D8 merge)
exec "$(dirname "$0")/dispatch-route-worker.sh" record "$@"
