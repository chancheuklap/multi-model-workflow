---
name: hillclimb
description: "Sustained, scientific improvement of one metric against a target: loop hypotheses with before/after measurement, a decision log, and one commit per accepted win. Distinct from Perf issue, which is a one-off fix."
---

# Hillclimb

**You own the metric and the experiment's integrity.** For sustained, iterative improvement of one measurable thing against a target. A one-off fix is diagnosing-bugs or perf-issue. This is the loop. Each attempt stays on this ticket.

Core discipline: one change, one measurement, keep or revert. Never stack untested changes, and never claim a win from code inspection. Use **principle-prove-it-works**.

Redact every secret before showing a measurement: write `<REDACTED>` in its place.

## 1. Ground the workload

Use **how** for the target, and name the realistic workload dimensions that can move the result (data size, history, state, concurrency). Select a case that reproduces the complaint. If no case reproduces it, fix the repro instead of hillclimbing. Then fix one metric, the direction that counts as better, and a checkable stop predicate that pairs a target with a floor on attempts so a lucky early win can't end the run (the example "at least 50% better than baseline and at least 10 iterations" is this shape). Use the numbers on the ticket when given, otherwise agree them.

## 2. Freeze the harness

Use **principle-build-the-lever**. Build the measurement harness, prove its sensitivity, then freeze it. Run contrasting realistic workloads and confirm the target case reproduces the symptom while easier cases separate as expected. If the harness cannot distinguish them, revise the workload or metric. Use **benchmark-checklist** before you freeze it, and make it print its error count and a count of the work done. Once frozen, one repeatable command emits the metric, sampled enough to clear the noise (median of N, not a single run). Record the baseline metric and a green run of the regression gate (the tests that must keep passing) before any change.

## 3. Open the decision log

A `decision.tsv`, one row per attempt: id, hypothesis, change, before, after, delta, tests, verdict (kept or reverted), note. Read it before each attempt. Keep it out of the tree (gitignored).

## 4. Ground each hypothesis

Ground each hypothesis in the workload from step 1, so it names a specific mechanism ("defer X off the boot path because it blocks first paint"), not "try memoizing something". For a perf metric, read the performance mantras in perf-issue and order hypotheses by them, cheapest first. Borrow only their order, not that skill's stop rule or its handoff.

When an attempt's interface is still open and the change crosses a function boundary, use **codebase-design** for Phase A, Phase B, and Phase C before writing that attempt.

## 5. Loop

One hypothesis per iteration, on this ticket's branch:

- Make the change here. Use **principle-guard-the-context-window**.
- When several independent hypotheses would write the same files, use **principle-separate-before-serializing-shared-state** and run them one at a time on this branch.
- Measure before and after with the frozen harness, and run the regression gate.
- Accept only when the metric moves past noise and the gate stays green. Otherwise revert the change in full. A tweak that "might help" is not kept.
- One commit per accepted fix, staging only the files you changed (`git add <files>`, never `-A`). Log the row either way, kept or reverted.

Each iteration ends in a check before the next begins. Use **principle-sequence-verifiable-units**.

## 6. Push past the first plateau

On a stall, several rejects in a row, pivot category, combine near-misses, re-read the source, or try something more radical before concluding the hill is climbed. Correctness and simplicity outrank the number. Revert a win that breaks behavior, and keep a simplification that holds the number. Use **principle-subtract-before-you-add** and **principle-minimize-reader-load**.

## 7. Stop

Stop when the predicate is met, or when the remaining ideas are marginal and not worth their cost. Don't relax the predicate to meet it, and don't quit while cheap untried hypotheses remain. If you are stuck, surface it instead of spinning.

## 8. Report

The PR record carries the metric and target, baseline to final with the percent delta, iterations run (kept vs reverted), each accepted fix, the `decision.tsv` path, and the best idea you would try next if pushed further.

Done when the predicate is met or the stuck state is on the report, every attempt is a row, and each accepted win is its own commit on this ticket.
