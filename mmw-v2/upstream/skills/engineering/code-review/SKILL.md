---
name: code-review
description: Review one ticket's diff from a base commit along three default axes — Standards, Spec, Tests — and UI when the session starts it, or review one named axis of that diff when started as a subagent. The session writes the axis reports as one review comment on the ticket. A session is given a base commit and a ticket number; an axis subagent is also given the axis name (Standards, Spec, Tests, or UI).
---

# Code review

Two doors, and this run is at one of them.

| You are | Read |
| --- | --- |
| The reviewer session: your prompt names this skill, a ticket and a base commit, and names no axis | [Running the session](references/session.md) — pin the diff, start the axes, sort the findings, write the ticket |
| An axis reviewer: your prompt names this skill, a ticket, a base commit, and one axis — Standards, Spec, or Tests | the matching file: [Standards](references/standards-reviewer.md), [Spec](references/spec-reviewer.md), or [Tests](references/tests-reviewer.md) |
| An axis reviewer: your prompt names this skill, a ticket, a base commit, and axis UI | [UI](references/ui-reviewer.md) |

The two sides are asymmetric on purpose. The session owns pinning the diff, starting the axes, sorting findings, and writing the ticket. Each axis owns what it looks for and writes nothing on the ticket.
