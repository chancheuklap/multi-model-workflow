### Bug fix

**You own this task. Plan, review, verify.**

Be scientific. Every shipped line traces to runtime evidence. Belt-and-suspenders that "might help" is a hypothesis, not a fix. It does not ship. When evidence refutes a hypothesis, revert what it motivated. The smallest change the evidence justifies ships, nothing more.

1. **Build a red loop.** Run the `diagnosing-bugs` skill on the bug. The **red loop** is that skill's tight feedback loop: one command that already goes red on *this* bug. Keep that command: **Verify on the same surface** runs it again.
   Done when one command goes red on this bug, and you have shown its invocation and its output.
2. **Find the root cause.** Trace the symptom to its cause with the `diagnosing-bugs` skill's ranked hypotheses and instrumentation, testing each probe against the red loop (**principle-fix-root-causes**). A guard that only silences the symptom turns the loop green and leaves the bug in the code. When two fixes that share one premise have already failed, write that premise down and question it before a third fix (**principle-attack-the-premise**).
   Done when you can state the cause in one sentence, and the red loop's output under a probe that could have refuted it supports that sentence.
3. **Choose the route.** Pick the route by the fix the cause needs. A small fix with a seam that reproduces the bug at its call site is made in this session test-first with the `tdd` skill, the minimised repro as its first failing test. Tell the user to run `/improve-codebase-architecture` when the real finding is that there's no good seam to lock the bug down. With no seam, make the fix in this session, and say in the reply that no regression test locks it. A fix that needs several sessions goes to **Write the spec** in **Write a spec and tickets**, with the cause and the red loop as its source, and this playbook ends here.
   Done when the fix is in place, its failing test first where a seam exists; or the user has heard that the fix needs several sessions and goes to **Write the spec** in **Write a spec and tickets**.
4. **Verify on the same surface.** Run the command from **Build a red loop** again, on the original scenario and on the surface where the bug was reported. "Inconclusive" or wrong-surface is not a pass. Flag it. Unit tests show branch behavior, not bug absence (**principle-prove-it-works**).
   Done when that command, run on the original scenario, passes, and its failing and its passing output are both kept for the reply.
5. **Deliver.** Run **Deliver a change**.
   Done when the fix is committed, or every step of the repository's own playbook that this session can take has run, and the user has heard each step that remains.

**Reply:** what was broken, root cause, fix, how you verified. Paste failing-then-passing repro output verbatim.
