---
name: correct
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Correct

The operator keeps correcting agents in this repo for the same mistakes. Plan a change that makes them impossible, for a worker to build after the owner's Go.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repo so a change that looks right from one file is right for the whole repo.

## Find the mistake classes

Open or take up the ticket as the mmw-mode skill's `references/ticket.md` `## Opening a ticket` says. For a registration, read `## Problem` and its `lesson.seen` occurrences, then the commits, reverts, review comments, agent instruction files, and workaround comments those occurrences cite. When the owner names the task without a registration, read recent commits, reverts, review comments, agent instruction files, and comments that explain workarounds. Record the past mistakes and their evidence in `## Problem`. Group the mistakes into classes. A class counts once it has happened twice. For a registered class, count occurrences from that registration's `lesson.seen` events; otherwise, count the evidenced past mistakes.

## Fix each class at the highest level that works

1. **Eliminate it with architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails. Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy.
2. **Enforce it with types so the bad state can't be written.** If bad code still compiles, add a lint or check, wired into the repository's `scripts/check`, whose error names the file, type, or function to use instead. If the pattern is already common, fail only when a change adds more.
3. **Test the behavior.** Fix or delete any test that still passes when the behavior it checks breaks, or that fails when only the internals change.
4. **Write a rule last, only for a judgment call.** Nothing fails when an agent skips it. One that holds in every repository goes into a principle; a fact of this repository into its glossary or an ADR; never into `AGENTS.md` or `CLAUDE.md`.

## Fix and prove

Choose the level under `## Fix each class at the highest level that works`. A correction whose rule is already written and enforced by nothing is a repeat. Plan its enforcement at the highest level that works, and the removal of the written rule once its mistake can't happen.

Write the plan and acceptance criteria into the ticket. Name the check to add to the repository's `scripts/check` and the real past mistake, with its commit, on which the check must first fail. Exceptions go on the offending line with a reason, an expiry date, and a human's approval. Hand the plan to the owner as the mmw-mode skill's `references/ticket.md` `## Handing it back` says. The worker builds it after the owner's Go. Done when the ticket holds the plan and runnable criteria and has been handed back.

**Verify.** Run the new check on the commit containing the real past mistake named in the ticket. It must fail for that mistake. Run it on the corrected head. It must pass. Include both commands, commits, and outputs in the reply.

**Reply:** each class with its evidence, the level you picked, and why a higher level didn't work; the plan, including the check to add and the past commit it must fail on; the acceptance criteria; and what the ticket leaves out.
