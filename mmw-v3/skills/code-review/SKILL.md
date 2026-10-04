---
name: code-review
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Code review

Whoever wrote this diff also wrote the tests that prove it, and watched them pass. This review is the first reading by anyone who did not write it: what it reports is fixed before the change is finished; what it misses ships.

You are given a request, a base commit and the axes to run. The request is a ticket, or a file holding the owner's request word for word. Send one subagent per axis, all at once, as mmw-mode's `## Subagents` says. Each subagent's prompt is its axis's file in full, with `ticket #<n>` or `the request in <path>` written in for `<request>`, and the base commit for `<base-commit>`:

| Axis | File |
| --- | --- |
| Standards | [references/standards-reviewer.md](references/standards-reviewer.md) |
| Spec | [references/spec-reviewer.md](references/spec-reviewer.md) |
| Tests | [references/tests-reviewer.md](references/tests-reviewer.md) |

Hold your turn until every axis has reported. Hand back each axis's report as it came, under the axis's name.
