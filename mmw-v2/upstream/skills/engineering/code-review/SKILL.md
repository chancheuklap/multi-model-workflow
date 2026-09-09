---
name: code-review
description: "Review one ticket's diff from a base commit along three axes — Standards, Spec, Tests — or review one named axis of that diff when started as a subagent. The session writes the three axis reports as one review comment on the ticket. A session is given a base commit and a ticket number; an axis subagent is also given the axis name (Standards, Spec, or Tests)."
---

# Code review

Two doors, and this run is at one of them.

| You are | Read |
| --- | --- |
| The reviewer session: your prompt names this skill, a ticket and a base commit, and names no axis | [Running the session](references/session.md) — pin the diff, start the three axes, sort the findings, write the ticket |
| An axis reviewer: your prompt names this skill, a ticket, a base commit, and one axis — Standards, Spec, or Tests | the matching file: [Standards](references/standards-reviewer.md), [Spec](references/spec-reviewer.md), or [Tests](references/tests-reviewer.md) |

The two sides are asymmetric on purpose. The session owns pinning the diff, starting the three axes, sorting findings, and writing the ticket. Each axis owns what it looks for and writes nothing on the ticket.
