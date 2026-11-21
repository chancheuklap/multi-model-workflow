---
name: code-review
description: "Review a project branch once across Standards, Spec, and Tests after its spec tickets land. Use only when the operator asks for a branch code review."
---

# Code review

Three fresh reviewers check a finished project branch, each on one axis. The review runs once. This skill returns the checked findings to its invoker and changes nothing.

## Frame

The operator names the project branch. The scope is the diff from its merge base with trunk to its tip. Record the tip as the reviewed commit.

Find the spec issue the branch's tickets draw on, and the execution tickets whose PRs merged into the branch. A ticket still open or a PR not merged is outside the review. List each as a limitation. When no spec issue exists, say `Spec: none` and skip the Spec axis.

## Fan out

Spawn one fresh subagent for each axis, in parallel, assigning each its own worktree at the reviewed commit. Follow [Subagents](../mmw-mode/SKILL.md#subagents). Use the model and settings from the current host’s `code review` entry in `~/.agents/mmwstack-models.md` (or the supplied rule file). Give each the diff, the reviewed commit, the spec and the landed tickets, the standards files that govern the changed paths, and the reference for its axis. The reviewer leaves the reviewed files unchanged and pushes nothing.

| Axis | Reference |
| --- | --- |
| Standards | [references/standards-reviewer.md](references/standards-reviewer.md) |
| Spec | [references/spec-reviewer.md](references/spec-reviewer.md) |
| Tests | [references/tests-reviewer.md](references/tests-reviewer.md) |

Wait for every report. A missing report is a limitation of this review, not a pass.

## Check

Check each finding against the reviewed commit. Do not review the diff again. Read the cited rule or requirement and the code. Keep a finding the commit supports. Drop one it does not, with the reason. Keep a runtime claim when a rerun shows the failure. When a reproduction cannot be rerun, mark it unverified and say why.

For each kept finding, name the approved requirement it affects. Say whether the evidence shows a defect this work introduced, an existing defect, or an uncertain cause. A valid finding does not authorize a repair by itself.

A **hard finding** is a documented-standard breach, a spec finding, or a test finding you kept. A **judgement call** is a baseline smell.

## Report

Use [unslop](../unslop/SKILL.md) for the report. Return to the invoker the reviewed commit and, for each axis, the supported finding count, the dropped findings with reasons, and what stayed unverified. Mark each kept finding a hard finding or a judgement call, and keep judgement calls under their axis.

Do not send the axes or any reviewer again. A second review needs a new request from the operator.
