---
name: correct
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Correct

The operator keeps correcting agents in this repo for the same mistakes. Change the repo so the next agent can't make them.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repo so a change that looks right from one file is right for the whole repo.

## Find the mistake classes

First, read recent commits, reverts, review comments, agent instruction files, and comments that explain workarounds. Group the mistakes into classes. A class counts once it has happened twice.

## Fix each class at the highest level that works

1. **Eliminate it with architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails. Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy.
2. **Enforce it with types so the bad state can't be written.** If bad code still compiles, add a lint or check, wired into the repository's `scripts/check`, whose error names the file, type, or function to use instead. If the pattern is already common, fail only when a change adds more.
3. **Test the behavior.** Fix or delete any test that would still pass if every function it calls returned nothing.
4. **Write a rule last, only for a judgment call.** Nothing fails when an agent skips it. One that holds in every repository goes into a principle; a fact of this repository into its `TESTING.md`, its glossary or an ADR; never into `AGENTS.md` or `CLAUDE.md`.

## Fix and prove

Then fix the most frequent classes now, one commit each. A correction whose rule is already written and enforced by nothing is a repeat: fix it at the highest level in the same change, and drop the written rule once its mistake can't happen. Prove each new check fails on a real past mistake. Run it through `scripts/check`, locally and in CI. Exceptions go on the offending line with a reason, an expiry date, and a human's approval.

**Reply:** each class with its evidence, the level you picked, and why a higher level didn't work.
