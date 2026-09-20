# Handing back a report

## Resolve `<engine>` once

`<engine>` is `scripts/verify-ticket.py`, resolved from this skill's own `SKILL.md` the way its **Resolve `<engine>` once** section says.

## The review report

You are the reviewer on ticket `<n>`, with the report written to a file.

```bash
<engine> <n> --review <file>
```

It posts the file as the review comment — the `reviewer.reported` event, carrying the two commits. That event is what wakes the worker waiting on your report: the relay of the `dispatch` skill reads it off the ticket and wakes the session that started you, so posting it is the whole of telling.

Before posting, the run checks the first line and every `## In-ticket` row. The first line is `REVIEW <base commit>..<HEAD commit>`; those commits become the event's `base` and `head`. An empty list is `None` or `None.`. Each finding row uses the `- <Standards|Spec|Tests|UI> <path>:<line> — <claim>` form, with its category and source when the review contract requires them. A report with an unknown nonempty row is refused here, before any event wakes the worker.

## Exit codes

`0` the comment is on the ticket. `2` the first line, file, or `## In-ticket` rows are invalid: nothing posted, the reason on stderr.
