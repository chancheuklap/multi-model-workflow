#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import json

message = (
    "For AgentFlow feature work, use to-issues to produce vertical large "
    "and small issues, use orchestrate-plan-writing to turn reviewed design "
    "and those issues into an issue-backed plan, then use orchestrate-workflow "
    "for Phase 0 review, Task Pack execution, "
    "review repair, root-cause routing, final intent verification, and "
    "business report."
)

print(json.dumps({"systemMessage": message}, ensure_ascii=False))
PY
