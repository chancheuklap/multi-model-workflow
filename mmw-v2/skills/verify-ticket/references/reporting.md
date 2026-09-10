# Handing back a report

## Resolve `<engine>` once

`<engine>` is `scripts/verify-ticket.py`, resolved from this skill's own `SKILL.md` the way its **Resolve `<engine>` once** section says.

## The review report

You are the reviewer on ticket `<n>`, with the report written to a file.

```bash
<engine> <n> --review <file>
```

It posts the file as the review comment — the `reviewer.reported` event, carrying the two commits. That event is what wakes the worker waiting on your report: the relay of the `dispatch` skill reads it off the ticket and wakes the session that started you, so posting it is the whole of telling.

The first line decides whether anything is posted at all. A file that does not open `REVIEW <base commit>..<HEAD commit>` is refused and nothing lands on the ticket, so nothing wakes the worker either, because those two commits are the event's `base` and `head`: a report that names no commits does not say which diff it read. An empty file is refused the same way.

## Exit codes

`0` the comment is on the ticket. `2` the first line was wrong or the file was empty: nothing posted, the reason on stderr.
