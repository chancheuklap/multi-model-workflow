---
name: code-review
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Code review

The session that wrote this diff wrote the tests that prove it and watched them pass. This review is the first reading by anyone who did not write it: what it reports is fixed before the change lands; what it misses ships.

## Find your moment

| You are | Read |
| --- | --- |
| The reviewer of a ticket: your start prompt is `Dispatched: reviewer, ticket #<n>, base <commit>` | [Running the session](references/session.md): pin the diff, start the axes, verify the findings, sort them, write the report on the ticket |
| Asked to review a change that has no ticket | Step 3 of the **mmw-mode** skill's Shared closing playbook: the request written to a file, the four axes started on it, each finding verified as [Running the session](references/session.md) step 3 says; report each finding with its verdict to whoever asked |
| One axis: your prompt names one of these files | [Standards](references/standards-reviewer.md), [Spec](references/spec-reviewer.md), [Tests](references/tests-reviewer.md) or [Correctness](references/correctness-reviewer.md) |
