---
name: code-review
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Code review

The session that wrote this diff wrote the tests that prove it and watched them pass. This review is the first reading by anyone who did not write it: what it reports is fixed before the change lands; what it misses ships.

## Find your moment

| You are | Read |
| --- | --- |
| The reviewer of a ticket: your start prompt begins `Dispatched: reviewer, ticket #<n>, base <commit>` | [Running the session](references/session.md): pin the diff, start the axes, verify the findings, sort them, write the report on the ticket |
| Asked to review a pull request someone else opened | [Running the session](references/session.md) through verifying each finding, with the pull request's description written to a file that each axis reads in place of a ticket, and the pull request's base for the base commit; fix nothing, and report each finding with its conclusion to whoever asked |
| One axis: your prompt names one of these files | [Standards](references/standards-reviewer.md), [Spec](references/spec-reviewer.md), [Tests](references/tests-reviewer.md) or [Correctness](references/correctness-reviewer.md) |
