### Revising a spec

**You own the revised section and every unlanded ticket cut from it.**

A section of a spec already on the tracker has to change: a mechanism added under **How a test arrives at a state**, a decision under `## Implementation Decisions` altered, a judgement written into one of its subsections. Edit that spec, never publish a new one: a new issue gets a new number, and every ticket's **Parent** points at the old one. A published spec, a ticket body and its acceptance criteria are edited only by the night's orchestrator, within Run a night's authority order, or by a session the user is working in. Read the issue with its full body and comments; write the replacement body with `gh issue edit <spec> --body-file <file>`.

1. **Rewrite the section.** Read the issue body in full, rewrite the section so it reads as if written that way from the start, and write the body back. Done when the issue body reads as if written that way from the start. The section follows **principle-files-describe-the-present**; what changed goes in step 2's comment.
2. **Say what changed.** What changed and why goes in one comment on the spec. Done when that comment is posted.
3. **Bring the tickets along.** Tickets already cut from the section and not yet landed are checked against the new text and corrected where they no longer match; a landed one is followed by a correction ticket, cut with the **to-tickets** skill on this spec. A criterion whose premise disappears is taken out of its ticket's `## Acceptance criteria` rather than left there without a command; the number is not reused, and a comment on the ticket says what became of it. Done when every ticket cut from the section and not yet landed matches the new text, and each landed one that no longer matches has its correction ticket published. The revised spec is the new baseline the tickets copy (**principle-baseline-is-the-contract**).

**Reply:** the spec by name with its link, the section changed and why, and each ticket corrected or opened, by name.
