# AgentFlow Full-Lifecycle Dry Run

Read-only dry run. Do not edit files. Do not run destructive commands. Do not merge, push, or create a PR.

Working directory: `/Users/cheuklapchan/agentflow`

Use the installed `orchestrate-workflow` behavior. Confirm Codex can see `orchestrate-workflow`, then read the visible `SKILL.md` before selecting sample docs.

## Required Reads

Read these live project documents first:

- `AGENTS.md`
- `PROJECT.md`
- `ENGINEERING-RULES.md`
- the visible `orchestrate-workflow` `SKILL.md` path, usually from `$HOME/.agents/skills/orchestrate-workflow/SKILL.md` for user-level installs

Then use `rg --files docs/superpowers/specs docs/superpowers/plans` to choose current, real documents:

- one ordinary UI / endpoint / Console task when available;
- one high-risk runtime / billing / migration / browser takeover task when available.

If only one suitable document set exists, say so and explain the sampling limitation.

## Output Required

Return a dry-run report with:

1. Documents selected and evidence that they are current files.
2. Phase 0a design review routing: which reviewers, which task facts, project anchors, and risk flags they would receive.
3. Phase 0b plan review routing: coverage, compliance, second-opinion checks.
4. Task Pack grouping: tasks, likely owned files, dependencies, risk, serial/parallel decision, AFK/HITL classification.
5. Worker routing: `coding_worker` vs `complex_coding_worker`, with reason.
6. Pack review and repair loop: how findings return through `send_input` to the same worker, and when to escalate.
7. Root-cause route: how a maintenance bug enters via feedback loop / bug brief / reproduction before a fix.
8. Final intent verification: focused pytest, release-gate, VM remote smoke, browser/manual checks, and what each proves.
9. Phase C business report shape.
10. Confirmation that the dry run does not require manual phase commands and does not attempt merge/push/PR.

Ground every claim in the live documents you read. If a path or command is an inference, label it as an inference.
