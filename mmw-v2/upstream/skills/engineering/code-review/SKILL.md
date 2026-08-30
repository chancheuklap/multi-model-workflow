---
name: code-review
description: "Review the changes since a base commit along three axes: Standards (does the code follow this repo's documented coding standards?), Spec (does the code match what the originating ticket or spec asked for?), and Tests (are the test cases the criteria name worth trusting?). Runs the three reviews in parallel sub-agents and reports them on the ticket. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\"."
---

You are the dispatcher. You run three read-only sub-agents over one diff and write their reports onto one ticket. You review nothing yourself.

Invoked as `code-review <base-commit> #<ticket>`. Both arguments come from the caller; when either is missing, ask for it.

Read [`references/dispatch.md`](references/dispatch.md) and do what it says. It carries the git commands, how to launch the three sub-agents, how to sort their findings, and the exact shape of the comment you post.

The three sub-agents each read one reference and nothing else from you:

- Standards → [`references/standards-reviewer.md`](references/standards-reviewer.md)
- Spec → [`references/spec-reviewer.md`](references/spec-reviewer.md)
- Tests → [`references/tests-reviewer.md`](references/tests-reviewer.md)

Each prompt you send carries three values and no prose: the base commit, the ticket number, and the path to that agent's reference. Everything fixed — what to look for, where to find the repo's standards, how to reach the spec, which test files are in scope — is already written in the reference file, and the sub-agent reads it itself. Pasting any of it into the prompt puts a second copy in play that drifts from the first.

## Why three axes

One change can pass one axis and fail another:

- Follows every convention, builds the wrong thing → **Standards pass, Spec fail.**
- Builds exactly what was asked, breaks the project's conventions → **Spec pass, Standards fail.**
- Does the right thing, proved by a test that would pass either way → **Standards and Spec pass, Tests fail.**

Each axis reports separately so one cannot mask another. You present them side by side and rank nothing across them.

## The ticket is where reports live

The reviewers ran in a session that ends; the ticket outlives it, and the worker who fixes these findings reads the ticket, not your transcript. A report that exists only in this conversation reaches nobody.
