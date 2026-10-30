---
name: correct
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Correct

The operator keeps correcting agents in this repo for the same mistakes. Plan a change that makes them impossible, for a worker to build after the owner's Go.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repo so a change that looks right from one file is right for the whole repo.

## Find the mistake classes

Open or take up the ticket as the **to-tickets** skill's opening entry says. For a registration, read `## Problem` and its `lesson.seen` occurrences, then the commits, reverts, review comments, agent instruction files, and workaround comments those occurrences cite. When the owner names the task without a registration, read recent commits, reverts, review comments, agent instruction files, and comments that explain workarounds. Record the past mistakes and their evidence in `## Problem`. Group the mistakes into classes. A class counts once it has happened twice. For a registered class, count occurrences from that registration's `lesson.seen` events; otherwise, count the evidenced past mistakes.

## Fix each class at the highest level that works

Choose the fix per **principle-encode-lessons-in-structure**. Wire a new lint or check into the repository's `scripts/check`; its error names the file, type, or function to use instead. If the pattern is already common, fail only when a change adds more. Apply **principle-test-behavior-not-implementation** to the tests that prove the fix.

When only judgment can address the mistake, put cross-repository guidance in a principle and a repository fact in its glossary or an ADR; never in `AGENTS.md` or `CLAUDE.md`.

## Fix and prove

Record the mechanism chosen under `## Fix each class at the highest level that works` and why a stronger one does not fit.

Write the plan and acceptance criteria into the ticket. Name the check to add to the repository's `scripts/check` and the real past mistake, with its commit, on which the check must first fail. Exceptions go on the offending line with a reason, an expiry date, and a human's approval. Use the **to-tickets** skill's independent entry for the prepared plan, then hand it to the owner under the mode's preparation authority rules. Add `needs-triage` while their decision remains. The worker builds it after the owner's Go. Done when the ticket holds the plan and runnable criteria and has been handed back.

**Verify.** Run the new check on the commit containing the real past mistake named in the ticket. It must fail for that mistake. Run it on the corrected head. It must pass. Include both commands, commits, and outputs in the reply.

**Reply:** each class with its evidence, the level you picked, and why a higher level didn't work; the plan, including the check to add and the past commit it must fail on; the acceptance criteria; and what the ticket leaves out.
