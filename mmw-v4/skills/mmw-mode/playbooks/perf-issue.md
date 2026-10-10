### Perf issue

**You own the measurement story. Plan, review, verify the numbers.** Tie every fix to a measurement, don't read source instead of measuring.

1. Capture a baseline trace via the matching control skill. Vet the baseline, and each later number, with the **benchmark-checklist** skill.
2. `how` to ground hypotheses. Don't claim a perf ceiling without running it first. Read the code on the hot path before naming a cause (**principle-read-before-you-conclude**).
   Try the performance mantras in order, cheapest first:
   1. Don't do it. Stop work whose result nothing uses rather than cheapening it.
   2. Do it, but don't do it again.
   3. Do it less.
   4. Do it later.
   5. Do it when they're not looking.
   6. Do it concurrently.
   7. Do it cheaper.

   When an earlier mantra meets the target, stop.
3. Plan the fix from the trace. If it crosses a function boundary, `architect` first.
4. Write the ticket and send it. Write one ticket in the shape of `../references/ticket.md`, with `None` under **Parent**. **What to build** states the baseline number, the trace evidence, the planned change and the target, and asks for one attempt at a time, each verified before the next (the **sequence-verifiable-units** principle skill). The first acceptance criterion is the benchmark command, vetted with the **benchmark-checklist** skill, printing a line only a run that meets the target prints; the second, the tests the change must keep green. Publish it with `gh issue create`, with the labels `mmw:ticket`, `ready-for-agent` and one worker label (`junior-worker`, or `senior-worker` for silent-failure work), creating any the repository lacks as `../references/github-issues.md` says, then run `verify-ticket.py <n> --lint` of the **verify-ticket** skill and fix every `ERROR`. Then run **One ticket** of the Run a night playbook (`playbooks/run-a-night.md`) on it: it cuts the ticket's own branch, sends the worker, and ends your turn. Done when the ticket is published with no `ERROR` and the worker is sent.
5. Measure it again. Woken by `#<n> ticket.passed`, capture a post-fix trace in the ticket's worktree (`.worktrees/issue-<n>`) the way step 1 captured the baseline, then parse and compare the artifacts (JSON to sqlite, diff). "Inconclusive" or wrong-surface is not a pass. Flag it. A target the numbers miss is reported as missed, never met by changing the benchmark (**principle-fix-root-causes**): land nothing, and tell the user. Woken by `#<n> ticket.returned`, the worker handed it back: read why on the ticket, `land` it as **One ticket** step 4 says, and tell the user. Done when the post-fix numbers are compared with the baseline, or the user has been told why nothing lands.
6. When step 5 found the target met, deliver it as **One ticket** steps 4 and 5 say: `land`, then one pull request citing the measurement, merged on the user's yes. Done when the pull request is merged, or the user has its link and has not said yes.

For sustained improvement against a metric rather than a one-off fix, use the Hillclimb playbook (`playbooks/hillclimb.md`).

**Reply:** baseline number, post-fix number, delta, artifact path.
