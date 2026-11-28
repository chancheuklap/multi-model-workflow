---
name: arena
description: "Run two parallel candidates, pick a base, and graft the losers' best parts. Use for 'throw it in the arena' or non-trivial artifacts risking the wrong shape."
---

# Arena

Start a checklist with one entry per phase (Frame, Fan out, Cross-judge, Pick, Graft, Verify) before launching anything.

## Phase A: Frame

Every candidate gets the same prompt, so the prompt is the contract. When the task assigns each candidate a design direction, the direction is the only line that differs.

1. State the artifact each candidate is producing. For an implementation, include the execution ticket URL in the task each candidate receives. When the candidates will write or change tests, put the expected behavior and “Invoke [write-tests](../write-tests/SKILL.md) before writing or changing tests” in their shared prompt.
2. Derive the rubric, 3-6 concrete gradeable criteria for what success looks like on *this* task. It is the picker's tool in Phase D. Candidates only see the task.
3. Use the model and settings from the current host’s `arena runners` entry in `~/.agents/mmwstack-models.md` (or the supplied rule file). Use exactly two entries, one per runner, including repeats. If more design directions are proposed, choose the two that best distinguish the alternatives; do not add runners.
4. Give each candidate its own output location that the parent and judge can read (a git worktree where possible, otherwise `/tmp/arena-<slug>/candidate-<n>/`), per the [principle-separate-before-serializing-shared-state](../principle-separate-before-serializing-shared-state/SKILL.md) principle skill.

## Phase B: Fan out

Spawn both runners in parallel, each in a fresh context. Follow [Subagents](../mmw-mode/SKILL.md#subagents) and [host-dispatch](../host-dispatch/SKILL.md). Give each only the task, the path to the shared grounding, its own output path, and instructions to produce the artifact and a short rationale naming the alternatives it considered and what it rejected.

If a candidate produces no output, continue with the remaining candidate and note the dropout.

## Phase C: Cross-judge

After all Phase B candidates complete, spawn one fresh read-only judge that produced none of the candidates, following [Subagents](../mmw-mode/SKILL.md#subagents) and [host-dispatch](../host-dispatch/SKILL.md). Use the first available entry in pool order (including an explicitly inherited model) from the current host's `arena cross-judge pool` line in `~/.agents/mmwstack-models.md` (or the supplied rule file). If none runs, pick the base yourself in Phase D and say the judge did not run. While you read in Phase D, the judge scores each candidate by path label on each rubric criterion and recommends a base with rationale. Never spawn the judge while candidates are still writing.

## Phase D: Pick a base

Read every candidate end to end before picking. Score each against the rubric criterion by criterion, not on holistic feel, and compare with the cross-judge when Phase C ran one. Agreement on the base confirms the pick. Disagreement means one of you is biased or the rubric was ambiguous. Read both rationales before deciding.

Pick the base a future maintainer can extend most easily without breaking invariants. When two feel tied, prefer the cleaner boundary or smaller API, per [principle-laziness-protocol](../principle-laziness-protocol/SKILL.md).

## Phase E: Graft

Walk each losing candidate once more for what is worth porting into the base, usually one or two things per candidate, not most of it. Fold each graft in by hand, per the [principle-redesign-from-first-principles](../principle-redesign-from-first-principles/SKILL.md) principle skill, so the result stays coherent under one mental model. Don't paste mechanically.

If the candidates converge on one shape, that is strong agreement. Note it and ship the consensus shape. No graft is needed. If they wildly diverge without assigned directions, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase F: Verify

Verify the synthesized artifact like any other output, per the [principle-prove-it-works](../principle-prove-it-works/SKILL.md) principle skill. If verification finds a problem the arena missed, either Phase A was wrong (re-frame and re-run) or a candidate caught it and you missed the graft (go back to Phase E). Don't paper over it.

## Outputs

One synthesized artifact, with a short synthesis note alongside naming the base and why, the cross-judge's verdict or that Phase C skipped the judge, each graft with its source candidate, what was rejected and why, any convergence or dropouts, and the verification result.
