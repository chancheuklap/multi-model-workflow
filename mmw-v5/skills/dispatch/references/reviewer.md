# Reviewer

Your assignment is the three-axis review of one committed comparison. The brief names the pinned comparison as `base` and the commit to review as `head`. A ticket send names the same two values in its prompt.

Read the spec and the other sources named in the assignment. Call the Skill tool with "code-review" for the main reviewer. Keep its preparation, three independent axes, and report intact. Supply that pinned comparison and that commit. Confirm HEAD is `head` before reviewing. A mismatch is an unavailable review.

The verifier runs `verify-<app>`. This review does not.

For its native axis subagents, use the [common tools operation](../SKILL.md#use-this-runs-tools) with row `review-axis` and this session's actual HOST. Each axis is told to call the Skill tool with "code-review" for its assigned reviewer, with the same pinned comparison. These are native subagents, not independent `dispatch.sh send` sessions.

The checked complete report is your assignment result. Return it through the report command under [Return the assigned result](../SKILL.md#return-the-assigned-result), with the actual base and head. State an invalid comparison or an incomplete review. You report findings. You do not fix the reviewed output.
