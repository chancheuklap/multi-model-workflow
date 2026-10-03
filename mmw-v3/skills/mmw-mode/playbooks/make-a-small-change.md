### Make a small change

**The user checks this change directly.**

This playbook builds and delivers a change with no spec, no tickets and no night. This path has none of what a ticket brings: no criteria a script runs, no reviewer in a session of its own, no closed ticket as the record. So what this session misses reaches the user, unless a reader who did not write the change finds it first. The temptation is to call the change too small for that reader; run **Get a second reading** however small it is.

1. **Write it test-first.** Run the `tdd` skill in this session, to build a concrete behaviour test-first without a spec or tickets. The code you write follows `references/code-writing-rules.md`. A test that would still pass with the change undone gives the user's check nothing to stand on (`principles/principle-test-behavior-not-implementation.md`).
   Done when every behaviour the change adds or alters has a test at a seam the user confirmed, and each of those tests failed before its code was written and passes now.
2. **Run the checks.** Run type checks and single test files regularly while you work. At the end, run the repository's type checks, and its tests as `references/running-checks.md` says.
   Done when, on the final code, the repository's type checks and the tests it names for this change pass, and each run's output shows it ran tests that reach the changed code.
3. **Get a second reading.** Commit the change to the current branch: the `code-review` skill reviews the commits between its fixed point and `HEAD`. Run it with the commit this change started from as its fixed point, and the user's request, pasted word for word, as its spec: its reviewers cannot read this conversation. Do not tell it which parts you believe are right: the user would then check a change only you have judged (`principles/principle-a-second-reader-judges.md`). Check each finding against the code before you act on it: fix what holds, and keep what does not for the Reply with your reason. On a host that cannot start a subagent, tell the user to run the `code-review` skill in a new session with the same fixed point and request, and list the second reading in the Reply as not done until that session's answer comes back. Reading the change again in this session is not a second reading.
   Done when both of its reports have returned and each finding is fixed or kept for the Reply with a reason, or, on a host that cannot start a subagent, the user has what to run and the Reply lists the second reading as not done.
4. **Deliver.** Run `playbooks/deliver-a-change.md`.
   Done when that playbook is done.

**Reply:** what changed; how it was verified, naming the checks and tests that ran; why each new file or dependency was needed; what the user should check; and, while the second reading is still with a new session, that it is not done.
