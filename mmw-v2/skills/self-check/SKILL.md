---
name: self-check
description: Worker's own cleanup pass over the code it just wrote, run before any acceptance gate — the implement skill names it at that step. Use when you have finished implementing a ticket and are about to run its gates, or when a ticket's worker asks to "self-check" before handing off. Eight local items, behaviour-preserving, architecture untouched.
---

# Self-check

You wrote this code minutes ago and still hold the context: which name you picked under pressure, which helper you copied instead of calling, which comment stopped being true after the third rewrite. That context is the whole value of this pass — a verifier starting cold cannot see it. Run the pass on your own output, then go to the gates.

The eight items are the **cleaner** role's local cleanup scope from swarm-forge, quoted verbatim (source: `docs/specs/landing-closeout/discipline-sources.md`, chapter 3, `sf-six-pack/swarmforge/roles/cleaner.prompt`, commit b933d68). The role's own boundaries are quoted with them and hold here unchanged.

## The pass

Walk every file you touched, once per item, in this order:

> - Improve local code clarity before architectural review: names, function cohesion, local coupling, duplication, complexity, test readability, stale comments, and dead code.

1. **names** — > Rename functions, variables, files, modules, tests, and helpers when better names make intent clearer.
2. **function cohesion** — > Split functions or files that mix unrelated local responsibilities, but leave high-level dependency direction and architectural boundary decisions to the architect.
3. **local coupling** — > Reduce unnecessary parameter chains, shared mutable state, and knowledge of unrelated modules.
4. **duplication** — a helper that already lives in the codebase replaces the copy you wrote.
5. **complexity** — > Keep refactors small enough to verify locally.
6. **test readability** — > Clean test names, setup, fixtures, helpers, and assertions without changing behavior.
7. **stale comments** — a comment states only rationale that is still true; one that narrates a version of the code that no longer exists is deleted.
8. **dead code** — code nothing reaches after your change is deleted, not commented out.

Items 4, 7 and 8 are the names from the scope line above; the cleaner prompt gives them no sentence of their own, so the one-line reading here is ours.

## Boundaries

Quoted from the same role, and binding:

> - Preserve behavior while improving names, duplication, boundaries, and testability.
> - Do not introduce new behavior.
> - Make local error paths explicit and consistently named without changing error-handling policy.

"The architect" in item 2 is a swarm-forge role this workflow does not have. Read it as: dependency direction and module boundaries are decided by the ticket and its spec, not by this pass. If the pass makes you want to move a boundary, leave it and record the observation in your final report.

## Completion

The pass is complete when every touched file has been walked against all eight items and the tests that covered the code before the pass still pass after it. Then run the ticket's gates.
