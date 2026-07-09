#!/usr/bin/env bash
# 兼容入口:转 worker.sh(宿主中立)
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"
exec bash "$D/worker.sh" "$@"
