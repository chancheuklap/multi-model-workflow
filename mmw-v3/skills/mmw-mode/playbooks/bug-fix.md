### Bug fix

**You own this task. Plan, review, verify.**

Be scientific. Every shipped line traces to runtime evidence. Belt-and-suspenders that "might help" is a hypothesis, not a fix. It does not ship. When evidence refutes a hypothesis, revert what it motivated. The smallest change the evidence justifies ships, nothing more.

1. **Diagnose and fix.** Run the `diagnosing-bugs` skill on the bug, through its fix and its cleanup. A guard that only silences the symptom turns the loop green and leaves the bug in the code. A bug that appears only after a restart is first suspected of stale persistent state: config files, caches, lock files. When two fixes that share one premise have already failed, write that premise down and question it before a third fix (`principles/principle-attack-the-premise.md`). The same pattern found elsewhere is listed for the Reply, not fixed. When the skill finds no correct seam for a regression test, make the fix in this session, say in the reply that no regression test locks it, and tell the user to run `/improve-codebase-architecture`. A fix that needs several sessions needs a spec: tell the user so, with the cause and the feedback loop as its source, and this playbook ends here. A unit test shows branch behaviour, not that the bug is gone: the feedback loop decides, run on the original scenario on the surface where the bug was reported. "Inconclusive" or wrong-surface is not a pass.
   Done when every item of the skill's cleanup checklist holds, its commit-message item apart, which **Deliver** meets, with the loop run on the original scenario on the reported surface and its failing and its passing output kept for the reply; or the user has heard that the fix needs several sessions and a spec.
2. **Run the checks.** Run the repository's tests as `references/running-checks.md` says, so the fix is known not to break what they cover.
   Done when the tests the repository names for the changed code pass.
3. **Deliver.** Run `playbooks/deliver-a-change.md`. The commit message states the hypothesis that turned out correct.
   Done when that playbook is done.

**Reply:** what was broken, root cause, fix, how you verified. Paste failing-then-passing repro output verbatim. List the same pattern found elsewhere, unfixed.
