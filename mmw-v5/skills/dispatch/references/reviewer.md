# Reviewer

Your assignment is the complete review of the supplied ticket and committed candidate. The script supplies the fixed point (`base`), expected reviewed `head`, target and exact report command.

Read the ticket and comments, its relevant parent-spec requirements and additional assignment input. Then invoke this v5 runtime's [code-review](../../code-review/SKILL.md) and follow its [complete-review process](../../code-review/SKILL.md#complete-review). Keep its preparation, three independent axes, verification and report intact. Use the supplied fixed point; confirm HEAD is the supplied candidate before reviewing. A mismatch is an unavailable review, not permission to review other output unnoticed.

For its native axis subagents, use the [common tools operation](../SKILL.md#use-this-runs-tools) with row `review-axis` and this session's actual HOST. Each axis receives the absolute paths to this runtime's `code-review/SKILL.md` and its assigned review reference, and the same pinned comparison. These are native subagents, not independent `dispatch.sh send` sessions.

The checked complete report is your assignment result. Return it through the report command under [Return the assigned result](../SKILL.md#return-the-assigned-result), with the actual supplied base/head. State an invalid comparison or incomplete review explicitly rather than claiming a clean result. You report findings; you do not fix the worker's output.
