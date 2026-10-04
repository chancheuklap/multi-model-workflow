---
name: code-review
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Code review

A worker wrote this diff and the tests that prove it, and watched them pass. This review is the first reading by anyone who did not write it: what it reports, the worker fixes before the ticket closes; what it misses ships.

You are given a ticket, a base commit and the axes to run. Send one subagent per axis, all at once, as mmw-mode's `## Subagents` says. Each subagent's prompt is its axis's file in full, with the ticket number written in for `<ticket>` and the base commit for `<base-commit>`:

| Axis | File |
| --- | --- |
| Standards | [references/standards-reviewer.md](references/standards-reviewer.md) |
| Spec | [references/spec-reviewer.md](references/spec-reviewer.md) |
| Tests | [references/tests-reviewer.md](references/tests-reviewer.md) |
| UI | [references/ui-reviewer.md](references/ui-reviewer.md) |

Hold your turn until every axis has reported. Hand back each axis's report as it came, under the axis's name.
