# Cutting something out of a ticket

## Resolve `<engine>` once

`<engine>` is `scripts/verify-ticket.py`, resolved from this skill's own `SKILL.md` the way its **Resolve `<engine>` once** section says.

## When something has to leave this ticket

```bash
<engine> <n> --sub-issue <kind> <file>
```

`--sub-issue` takes a kind (`baseline`, `outside-owns`, `review`, `decision`, or `pipeline`) and a file whose first line is the title. It opens a new issue labelled `needs-triage`, parented to this ticket, whose own first line is `SUB-ISSUE <kind> from #<n>`, and posts a `child.opened` event on this ticket naming the new issue and its kind — the ticket's events are where its children are counted.

The kind says what was cut out: a baseline under `## Read first` that does not fit; a change outside `## Owns` that was merely convenient; an out-of-ticket finding from the review comment; a question whose answer would change what this ticket delivers; or a fault in the pipeline itself. An empty file, or a kind that is not one of the five, is refused and nothing is opened.

## Exit codes

`0` the sub-issue is open and recorded. `1` the sub-issue is open and its `child.opened` event could not be written; stderr names it — do not open it again. `2` a refusal, with the reason on stderr.
