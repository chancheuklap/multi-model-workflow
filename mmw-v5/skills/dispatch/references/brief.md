# Brief assignment

You have been sent a bounded task as `researcher`, `advisor` or `candidate`. Read the entire brief and any instructions file named by the first message. Follow the method the caller assigned; keep its scope, sources and required output. The role chooses the configured session, not a new task for you to invent.

If that method explicitly requires independent sessions, use [Send](../SKILL.md#send-an-independent-session) and [Wait](../SKILL.md#wait-read-and-acknowledge). Use native subagents only where the method calls for them. Keep each assignment understandable without this conversation.

Answer the actual question with the evidence, recommendation or artifact requested. Distinguish source inspection, execution and unverified inference. Name missing information that changes the answer. Preserve an owner-only choice in the result instead of blocking this unattended session on a chat question.

The copied brief includes the actual result destination and report command. [Return the assigned result](../SKILL.md#return-the-assigned-result): save the answer and execute that command successfully before ending. A method's final answer is not a replacement for the supplied delivery operation. The sender reads and acknowledges the batch result, then decides its next step.
