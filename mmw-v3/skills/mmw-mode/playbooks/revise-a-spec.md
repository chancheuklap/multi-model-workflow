### Revise a spec

**You own one change to a spec already on the tracker: its section rewritten in place, the reason left on the spec, and every ticket cut from that section brought into line.** The change is a mechanism added under **How a test arrives at a state**, a decision under `## Implementation Decisions` or `## Feature map changes` altered, or a judgement written into one of its subsections. A change to `## Feature map changes` follows the same steps as a change to `## Implementation Decisions`. A published spec is edited, never published again: a new issue gets a new number, and every ticket's **Parent** points at the old one. Only the orchestrator of a night on the spec, or a session the owner is working in, edits a published spec, a ticket body or its acceptance criteria. A spec that does not exist yet is written, not revised.

1. **Read the spec and what was cut from it.** Read the issue body in full, comments included, and list its tickets (`gh api --paginate repos/{owner}/{repo}/issues/<spec>/sub_issues?per_page=100`). Name the section that changes and every ticket cut from it.
   Done when you can name the section and each ticket cut from it, and whether that ticket has landed.
2. **Rewrite the section.** Rewrite it so the spec reads as if written that way from the start (**principle-files-describe-the-present**), and write the body back: `gh issue edit <spec> --body-file <file>`.
   Done when the issue body on the tracker reads as if written that way from the start.
3. **Say what changed and why.** Post one comment on the spec: what changed, why, and the issue, child or decision it came from.
   Done when the comment is posted.
4. **Bring the tickets into line.** Check each ticket cut from the section and not yet landed against the new text, correct it where it no longer matches, and lint it (`verify-ticket.py <n> --lint`, read as the `verify-ticket` skill's `references/linting.md` says). A criterion whose premise disappeared is taken out of `## Acceptance criteria` rather than left there without a command; its number is not reused, and a comment on the ticket says what became of it. A landed ticket the change contradicts is followed by a correction ticket, written as the `verify-ticket` skill's `references/ticket-format.md` says and published with `verify-ticket.py <spec> --publish --drafts <dir>` as Cut tickets step **Lint and publish the batch** says.
   Done when every ticket cut from the section and not yet landed matches the new text and lints with no `ERROR`.

**When the rows change.** When a later pull's `pull-report.md` records `增删控件或改流转`, and Write the screen contract's **Re-runs** rewrote the rows, the same holds row by row, and a new row gains one boundary criterion on the ticket that owns it.

**Reply:** the section that changed and why, and each ticket corrected, cut down, or followed by a correction ticket, with that ticket's number.
