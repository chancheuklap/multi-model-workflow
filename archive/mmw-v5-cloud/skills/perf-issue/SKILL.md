---
name: perf-issue
description: A measured slowness to trace and improve against a baseline.
---

# Perf issue

**You own the measurement story. Plan, review, verify the numbers.** Tie every fix to a measurement, don't read source instead of measuring.

Redact every secret before showing a trace or a measurement: write `<REDACTED>` in its place.

## 1. Capture a baseline

Capture a baseline trace on the surface where the slowness shows. Vet the baseline, and each later number: use **benchmark-checklist**.

## 2. Ground the hypotheses

Use **how** for the system to ground hypotheses. Read the evidence already in hand. Don't claim a perf ceiling without running it first.

Try the performance mantras in order, cheapest first:

1. Don't do it. Stop work whose result nothing uses rather than cheapening it.
2. Do it, but don't do it again.
3. Do it less.
4. Do it later.
5. Do it when they're not looking.
6. Do it concurrently.
7. Do it cheaper.

When an earlier mantra meets the target, stop.

## 3. Plan the fix

Plan the fix from the trace. Record whether the interface is still open and whether the fix crosses a function boundary; the ticket carries that to the Worker.

Use **principle-sequence-verifiable-units**, verifying each attempt before trying the next.

## 4. Hand off

Use **to-tickets** for the issue template. Use only that template as the ticket format, not that skill's interactive Process. One ticket. Blocked by: None (can start immediately). Use the worker-grade selection in the `Draft vertical slices` section from that same call.

What to build is the behaviour once the slowness is gone, tied to the baseline number and the mantra that met the target. State whether the interface is still open and whether the fix crosses a function boundary.

Acceptance criteria:

- [ ] The post-fix trace is vetted with benchmark-checklist, on the same surface as the baseline
- [ ] The artifacts are parsed and compared. "Inconclusive" or wrong-surface is not a pass
- [ ] The PR record carries the baseline number, the post-fix number, the delta, and the artifact path

For sustained improvement against a metric rather than a one-off fix, What to build is sustained improvement of one metric against a target, and it names the metric, the direction that counts as better, and the stop predicate.

Show the ticket to the user before publishing. Don't block on it; publish and proceed if the user is AFK.

Use **dispatch** and send this ticket as its Coordinator.

Done when the ticket is published and the Worker has been sent. The Worker implements the ticket.
