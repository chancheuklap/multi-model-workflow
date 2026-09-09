# Handing back a report

## Resolve `<engine>` once

`<engine>` is `scripts/verify-ticket.py`, resolved from this skill's own `SKILL.md` the way its **Resolve `<engine>` once** section says.

## The review report

You are the reviewer on ticket `<n>`, with the report written to a file.

```bash
<engine> <n> --review <file>
```

It posts the file as the review comment and, in the same call, tells the session that started you that the report has landed. One call because it is one act: a report on the ticket that the worker was not told about is a worker still asleep on a session that has already finished.

The first line decides whether anything is posted at all. A file that does not open `REVIEW <base commit>..<HEAD commit>` is refused, nothing lands on the ticket and nobody is told, because that line is the whole of what the worker matches on — both in the message and later on the ticket. An empty file is refused the same way.

## Exit codes

`0` the comment is on the ticket and the message has gone out. `2` the first line was wrong or the file was empty: nothing posted, the reason on stderr.
