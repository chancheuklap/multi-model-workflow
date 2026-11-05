#!/usr/bin/env bash
# Prepare MMW in this isolated cloud checkout before a new task starts.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host codex --cloud
