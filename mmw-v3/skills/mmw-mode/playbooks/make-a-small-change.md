### Make a small change

**The user checks this change directly.**

This playbook builds and delivers a change with no spec, no tickets and no night. This path has none of what a ticket brings: no criteria a script runs, no reviewer in a session of its own, no closed ticket as the record. So what this session misses reaches the user, unless a reader who did not write the change finds it first. The temptation is to call the change too small for that reader; run **Get a second reading** however small it is.

1. **Write it test-first.** Run the `tdd` skill in this session, to build a concrete behaviour test-first without a spec or tickets. A test that would still pass with the change undone gives the user's check nothing to stand on. A change that turns out to need several sessions needs a spec: stop, tell the user it goes to `playbooks/write-a-spec-and-tickets.md`, with what you found as its source, and this playbook ends here.
   Done when every behaviour the change adds or alters has a test, and each of those tests failed before its code was written and passes now; or the user has heard that the change needs several sessions and a spec.
2. **Verify it.** Run type checks and single test files regularly while you work. At the end, follow the `verify-this` skill in this session on the claim that the change does what the user asked, in the user's words.
   Done when `verify-this` has returned `VERIFIED` on the final code, or `INCONCLUSIVE` with its reason kept for the Reply.
3. **Get a second reading.** Commit the change: the `code-review` skill reviews the commits between its fixed point and `HEAD`. Run it with the commit this change started from as its fixed point, and the user's request, pasted word for word, as its spec: its reviewers cannot read this conversation. Do not tell it which parts you believe are right: the user would then check a change only you have judged. Check each finding against the code before you act on it: fix what holds, and keep what does not hold for the Reply with your reason. On a host that cannot start a subagent, tell the user to run the `code-review` skill in a new session with the same fixed point and request, and list the second reading in the Reply as not done until that session's answer comes back. Reading the change again in this session is not a second reading.
   Done when both of its reports have returned and each finding is fixed or kept for the Reply with a reason, or, on a host that cannot start a subagent, the user has what to run and the Reply lists the second reading as not done.
4. **Deliver.** Commit the change and tell the user.
   Done when the change is committed and the user has heard so.

**Reply:** what changed; the `verify-this` verdict and its evidence; why each new file or dependency was needed; what the user should check; and, while the second reading is still with a new session, that it is not done. When the change needs a spec instead, what you found that makes it need several sessions.
