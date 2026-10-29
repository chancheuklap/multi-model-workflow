### Perf issue

**You own the measurement story. Plan, review, verify the numbers.** Tie every fix to a measurement, don't read source instead of measuring. A worker makes the change, on one ticket.

1. **Open the ticket.** Open a ticket and its `fix-<n>` as `../references/ticket.md` `## Opening a ticket` says, with `Playbook: Perf issue` and the slowness in the owner's words under `## Problem`. A ticket already open keeps its number and opens only the `fix-<n>` it lacks. Done when the ticket is open and `fix-<n>` is on origin.
2. **Capture a baseline trace** via the matching control skill. Vet the baseline, and each later number, with the **benchmark-checklist** skill. Commit the benchmark command on `fix-<n>`. Done when the baseline number is vetted and its command is committed.
3. **Find the cause.** `how` to ground hypotheses. Don't claim a perf ceiling without running it first. Read the code on the hot path before naming a cause (**principle-read-before-you-conclude**).
   Try the performance mantras in order, cheapest first:
   1. Don't do it. Stop work whose result nothing uses rather than cheapening it.
   2. Do it, but don't do it again.
   3. Do it less.
   4. Do it later.
   5. Do it when they're not looking.
   6. Do it concurrently.
   7. Do it cheaper.

   When an earlier mantra meets the target, stop. Done when the trace shows where the time goes and which mantra answers it.
4. **Plan the change** from the trace. A question of code shape goes to the **prototype** skill's `## Pick a branch` first. Done when the change and its target number are planned.
5. **Write the ticket.** Fill it in as `../references/ticket.md` `## Opening a ticket` says. **What to build** states the baseline number, the trace evidence, the planned change and the target, and asks for one attempt at a time, each verified before the next (**principle-sequence-verifiable-units**). The first acceptance criterion is the benchmark command, vetted with the **benchmark-checklist** skill, printing a line only a run that meets the target prints; the second, the tests the change must keep green. Done when every section below `## Problem` is filled.
6. **Hand it back.** As `../references/ticket.md` `## Handing it back` says. Done when the owner has said go and One ticket runs, or the ticket is in `needs-triage` or closed.

**Measure it again.** One ticket step 4 runs this once the ticket passed: capture a post-fix trace in `.worktrees/issue-<n>` the way step 2 captured the baseline, then parse and compare the artifacts (JSON to sqlite, diff). "Inconclusive" or wrong-surface is not a pass. Flag it. A target the numbers miss is reported as missed, never met by changing the benchmark (**principle-fix-root-causes**).

**A ticket that came back.** When a ticket its worker handed back (a `ticket.returned` event) is picked from `needs-triage`, read why on the ticket and go back to step 3 with that evidence.

For sustained improvement against a metric rather than a one-off fix, use the Hillclimb playbook (`playbooks/hillclimb.md`).

**Reply:** the baseline number and its artifact path, the cause the trace shows, the planned change and its target, the criteria, what the ticket leaves out.
