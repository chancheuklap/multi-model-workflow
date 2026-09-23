# Revising a published spec

When a section of a spec already on the tracker has to change (a mechanism added under **How a test arrives at a state**, a decision under `## Implementation Decisions` altered, a judgement written into one of its subsections), edit that spec, never publish a new one: a new issue gets a new number, and every ticket's **Parent** points at the old one. Read the issue body in full, rewrite the section so it reads as if written that way from the start, and write the body back (`gh issue edit <n> --body-file <file>`). What changed and why goes in one comment on the spec. Tickets already cut from the section are checked against the new text and corrected where they no longer match. A published spec, a ticket body and its acceptance criteria are edited only by the main agent or the user.

A criterion whose premise later disappears is taken out of its ticket's `## Acceptance criteria` rather than left there without a command; the number is not reused, and the closing comment says what became of it.

## When the rows change

When a later pull's `pull-report.md` records `增删控件或改流转`, and the `write-screen-contract` skill's **Re-runs** have rewritten the rows:

- A ticket already cut and not yet landed has its criteria and **Read first** corrected to the new rows.
- A new row gains one boundary criterion on the ticket that owns it.
- A ticket already landed is followed by a correction ticket whose criterion is the same as the original's.

Done when the issue body reads as if written that way from the start, the comment saying what changed is posted, and every ticket cut from the section matches the new text.
