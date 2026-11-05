#!/usr/bin/env bash
# Prepare one user-level MMW installation for all repositories in this environment.
set -euo pipefail
host="${1:-codex}"
if [[ "$#" -gt 0 ]]; then shift; fi
if [[ "$#" == 0 ]]; then set -- "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; fi
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host "$host" "$@"
bash "$HOME/.agents/mmw/tools/dispatch/scripts/dispatch.sh" row researcher --host "$host"
