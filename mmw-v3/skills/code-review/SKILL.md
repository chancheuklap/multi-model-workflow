---
name: code-review
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Code review

Whoever wrote this diff also wrote the tests that prove it, and watched them pass. This review is the first reading by anyone who did not write it: what it reports is fixed before the change is finished; what it misses ships.

You are given a request, a base commit and the axes to run. The request is a ticket, or a file holding the owner's request word for word. Send one subagent per axis, all at once, so they never see each other's findings, as mmw-mode's `## Subagents` says. Each subagent's prompt is its axis's file in full, with `ticket #<n>` or `the request in <path>` written in for `<request>`, and the base commit for `<base-commit>`:

| Axis | File |
| --- | --- |
| Standards | [references/standards-reviewer.md](references/standards-reviewer.md) |
| Spec | [references/spec-reviewer.md](references/spec-reviewer.md) |
| Tests | [references/tests-reviewer.md](references/tests-reviewer.md) |
| UI, for a ticket whose criteria include a story criterion | [references/ui-reviewer.md](references/ui-reviewer.md) |

The Standards and Tests prompts also carry the repository's root `CODING_STANDARDS.md` at `HEAD`, in full, after the axis file. The Tests prompt then carries the repository's root `TESTING.md` at `HEAD`, in full. When a file is absent from `HEAD`, its place in the prompt holds one line: `This repository has no CODING_STANDARDS.md.` or `This repository has no TESTING.md.` Those rules reach the axes in their prompt, never as a file left for them to find, so an axis cannot settle for another document in their place.

Hold your turn until every axis has reported. Hand back each axis's report as it came, under the axis's name.
