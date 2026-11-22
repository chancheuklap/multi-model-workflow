### Perf issue

**You own the measurement story. Plan, review, verify the numbers.** Tie every fix to a measurement, don't read source instead of measuring.

1. Capture a baseline trace using the project's `verify-<app>` for the affected surface, or [verify-this](../../verify-this/SKILL.md) if none matches. Vet the baseline, and each later number, with the [benchmark-checklist](../../benchmark-checklist/SKILL.md) skill.
2. Trace the code to ground hypotheses. Don't claim a perf ceiling without running it first.
   Try the performance mantras in order, cheapest first:
   1. Don't do it. Stop work whose result nothing uses rather than cheapening it.
   2. Do it, but don't do it again.
   3. Do it less.
   4. Do it later.
   5. Do it when they're not looking.
   6. Do it concurrently.
   7. Do it cheaper.

   When an earlier mantra meets the target, stop.
3. Plan the fix from the trace. If it crosses a function boundary, [architect](../../architect/SKILL.md) first. Delegate implementation to a subagent. Use the model and settings from the current host’s `perf-issue` entry in `~/.agents/mmwstack-models.md` (or the supplied rule file). Review the diff. Capture a post-fix trace.
   Apply the [principle-sequence-verifiable-units](../../principle-sequence-verifiable-units/SKILL.md) principle skill, verifying each attempt before trying the next.
4. Parse and compare the artifacts (JSON to sqlite, diff). "Inconclusive" or wrong-surface is not a pass. Flag it.
   When the optimization touches `covered code` or guarded state (such as concurrency, locks, retries, or caching), run every matching project `formal verification skill` (`formal-verify-<area>` or a differently named skill covering that area) after the fix, sync any changed `model`, `formal verification harness`, and `coverage record` per [maintain-formal-verification-skill](../../maintain-formal-verification-skill/SKILL.md), prove `broken variant` failure on model updates, and confirm each `property` still holds.
5. Cite the measurement in the PR.
6. Run **Opening a PR**.

For sustained improvement against a metric rather than a one-off fix, use the Hillclimb playbook (`playbooks/hillclimb.md`).

**Reply:** baseline number, post-fix number, delta, artifact path.
