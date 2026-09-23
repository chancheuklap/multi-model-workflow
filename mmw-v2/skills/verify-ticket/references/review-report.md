# Posting a review report

`<engine>` is resolved in this skill's `SKILL.md`.

## The review report

You are the reviewer on ticket `<n>`, with the report written to a file.

```bash
<engine> <n> --review <file>
```

It posts the file as the review comment — the `reviewer.reported` event, carrying the two commits — which wakes the worker that started you.

Before posting, the run checks the first line and every `## In-ticket` row. The first line is `REVIEW <base commit>..<HEAD commit>`; those commits become the event's `base` and `head`. An empty list is `None` or `None.`. Each finding row uses the shape the `code-review` skill's `references/session.md` step 5 gives: `- <Standards|Spec|Tests|UI> [<category>] <path>:<line> — <claim> — source: <source>`. A report with an unknown nonempty row is refused here, before any event wakes the worker.

## Exit codes

`0` the comment is on the ticket. `2` the first line, file, or `## In-ticket` rows are invalid: nothing posted, the reason on stderr.
