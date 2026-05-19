#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import json

message = """[multi-model-workflow] Codex Orchestrate runtime active.

Entry routing:
- New feature, systemic bug, wrong state, PRD/issue/backlog, UI/UX feedback, screenshot feedback, test feedback, design/plan execution, existing diff review, or final validation -> use orchestrate-workflow as the entry gate.
- Missing reviewable design -> orchestrate-discovery.
- Reviewed design + issue hierarchy -> orchestrate-plan-writing.
- Reviewed plan + Task Pack inventory -> orchestrate-execution.
- Execution passed -> orchestrate-final-review.
- Multi-PR merge -> orchestrate-multi-pr-merge.

Runtime contracts:
- Phase skills live under .agents/skills/orchestrate-*/ and are progressively loaded. Read each reference only when the current step asks for it.
- Run state lives under .codex/multi-model-workflow/: scope-<run_id>.md, budget-<run_id>.json, active-run-id.
- Sub-agent dispatch must be self-contained. Custom agents do not read Orchestrate SKILL.md or references unless the parent provides an explicit path or pasted contract.
- Agent roles: plan_writer, coding_worker, complex_coding_worker, code_reviewer, release_reviewer, code_explorer, complex_code_explorer, root_cause_analyst, docs_worker.
- Baseline reviews use code_reviewer. Production-risk supplements use release_reviewer and never replace baseline review.
- Claude cross-model review follows orchestrate-workflow/references/external-review-lanes.md. Subscription-backed Claude review uses codex/reviewers/claude-subscription-review.sh, which invokes ordinary `claude` through stdin without `-p` and fixed `claude-opus-4-7` + `--effort high`; do not call `claude -p` unless the user explicitly authorizes Agent SDK / Extra Usage credits.
- Repair continuation should use send_input to the original agent when available; otherwise spawn the same agent_type with full context.

Hard gates:
- No verification evidence -> do not claim completion.
- No reviewable design -> do not jump to plan or worker.
- Design Review, Plan Review, Pack Review, Final Review are mandatory unless the entry gate explicitly selects Direct Repair.
- Upstream outputs from diagnose, prototype, improve-codebase-architecture, zoom-out, triage, grill-with-docs, and to-issues must be written back to the phase artifact before continuing.
- Without explicit user instruction, do not merge, push, open PRs, discard changes, or write production state.
- Commit boundary is rollback boundary: design/plan repair, reviewed Task Pack, accepted finding repair, and runtime sync are separate commits when committing is requested.
"""

print(json.dumps({"systemMessage": message}, ensure_ascii=False))
PY
