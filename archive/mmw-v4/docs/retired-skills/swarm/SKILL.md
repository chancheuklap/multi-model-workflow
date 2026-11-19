---
name: swarm
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Swarm

Fan out N parallel workers.

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
3. Set N from the user or derive it from the shape.
4. Give each worker its own writable output when it writes: a directory made with `mktemp -d`, named in its brief. A swarm writes no product code; a change to it is a ticket. When workers verify or measure commits, each brief names the exact SHAs. A measurement brief also names the method (sample count, what one sample is, order). The worker records both in its result.

## Phase B: Fan out

Send all N workers in one message, each a subagent on the `default` row as mmw-mode's `## Subagents` says, and hold your turn until every one has returned.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence. `PASS`: the slice or arm was checked as the brief says and nothing is wrong. `ISSUES`: the worker can prove a defect; it lists every issue it can prove, not only the first. `BLOCKED`: the check could not run, and the report says what stopped it.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

Read the terminal results. Drop a result that does not record the SHAs and method its brief names, and respawn that worker once. After a second miss, record a gap. A gap does not count as a pass. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.
