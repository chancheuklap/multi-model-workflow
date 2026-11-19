---
name: hillclimb
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# hillclimb

Sustain scientific improvement of one metric against a frozen target and attempt floor. One change, one measurement, keep or revert; correctness and simplicity outrank the number.

| Work in hand | Read |
| --- | --- |
| Choose workload, metric, harness and stop predicate | [Prepare](references/prepare.md) |
| Run the ticket's attempt loop | [Implement](references/implement.md) |
| Audit measured attempts and the final metric | [Verify](references/verify.md) |

## Attempt record

Each measured attempt is a ticket comment opening `Attempt <id>:` with hypothesis, change, before, after, delta, tests, verdict (kept or reverted) and note. The baseline is `Attempt 0`. The worker posts attempts, the reviewer reads them, and a criterion counts them with `gh api`. When preparation began before the execution ticket existed, the ticket writer records Attempt 0 there from the prepared baseline, linking its source. Subsequent attempts belong to that execution ticket.
