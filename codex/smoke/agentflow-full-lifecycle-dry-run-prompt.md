# AgentFlow Full-Lifecycle Dry Run

Read-only dry run. Do not edit files. Do not run destructive commands. Do not merge, push, or create a PR.

Working directory: `/Users/cheuklapchan/agentflow`

Use the installed `orchestrate-workflow` and `orchestrate-plan-writing` behavior. Confirm Codex can see both skills, then read the visible `SKILL.md` files before selecting sample docs.

## Required Reads

Read these live project documents first:

- `AGENTS.md`
- `PROJECT.md`
- `ENGINEERING-RULES.md`
- the visible `orchestrate-workflow` `SKILL.md` path, usually from `$HOME/.agents/skills/orchestrate-workflow/SKILL.md` for user-level installs
- the visible `orchestrate-plan-writing` `SKILL.md` path, usually from `$HOME/.agents/skills/orchestrate-plan-writing/SKILL.md` for user-level installs

Then choose current, real documents with a command that skips missing directories:

```bash
for d in docs/superpowers/specs docs/issues docs/orchestrate/plans; do
  [ -d "$d" ] && rg --files "$d"
done
```

- one ordinary UI / endpoint / Console task when available;
- one high-risk runtime / billing / migration / browser takeover task when available.

If only one suitable document set exists, say so and explain the sampling limitation.

## Output Required

Return a dry-run report with:

1. Documents selected and evidence that they are current files.
2. Phase 0a design review routing: which reviewers, which task facts, project anchors, and risk flags they would receive.
3. UI / UX mockup handling when the selected docs contain mockups: mockup paths, target viewports, key states, interaction, and verification evidence expected.
4. Issue-backed plan generation routing: source design, `to-issues` large issues, `to-issues` small issues, large issue -> small issue -> Task Pack mapping, missing-issue route if any, and plan output path.
5. Phase 0b plan review routing: coverage, compliance, second-opinion checks.
6. Task Pack inventory: task packs from plan, likely owned files, mockup anchors, dependencies, risk, serial/parallel decision, AFK/HITL classification.
7. Worker routing: `coding_worker` vs `complex_coding_worker`, with reason.
8. Pack review and repair loop: how findings return through `send_input` to the same worker, and when to escalate.
9. Root-cause route: how a maintenance bug enters via feedback loop / bug brief / reproduction before a fix.
10. Final intent verification: focused pytest, release-gate, VM remote smoke, browser screenshot / DOM / manual checks, and what each proves.
11. Phase C business report shape.
12. Confirmation that the dry run does not require manual phase commands and does not attempt merge/push/PR.

Ground every claim in the live documents you read. If a path or command is an inference, label it as an inference.
