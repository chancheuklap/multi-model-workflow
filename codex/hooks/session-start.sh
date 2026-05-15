#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import json

message = (
    "After Superpowers writing-plans produces a design or plan, use "
    "orchestrate-workflow for Phase 0 review, Task Pack execution, "
    "review repair, root-cause routing, final intent verification, and "
    "business report."
)

print(json.dumps({"systemMessage": message}, ensure_ascii=False))
PY
