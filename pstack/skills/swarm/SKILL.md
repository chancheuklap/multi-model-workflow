---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
disable-model-invocation: true
---

# Swarm

## Start

Start a checklist with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
3. Pick the worker model from the `swarm workers` line in the [pstack model rule](../setup-pstack/SKILL.md#model-rule). For a model race, name each arm's model from the user's configuration up front. Pick each subagent's reasoning level and fast or standard speed for the job, per the Subagents section of the [poteto-mode](../poteto-mode/SKILL.md) skill.
4. Give each writer its own output location and have it return artifacts the coordinator can open. When workers verify or measure commits, each brief names the exact SHAs. A measurement brief also names the method (sample count, what one sample is, order). The worker records both in its result.

## Phase B: Fan out

Spawn all N workers in parallel in the background, each on its own remote machine with its assigned model. Run a worker locally only when it needs access to something on the user's computer.

When a worker needs a non-default pushed branch, name it in the brief and have the worker check it out before starting.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Include the execution ticket URL when the worker will implement the change. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence. A worker that can prove a defect reports `ISSUES` and lists every issue it can prove, not only the first.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

Read the terminal results. Drop a result that does not record the SHAs and method its brief names, and respawn that worker once. After a second miss, record a gap. A gap does not count as a pass. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

## Phase D: Report

Return one consolidated in-chat report with a result table, issue one-liners, gaps or dropouts, and the race rule when used.
