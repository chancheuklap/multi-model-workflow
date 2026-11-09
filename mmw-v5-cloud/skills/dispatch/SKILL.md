---
name: dispatch
description: Coordinate an authorized spec or ticket, carry out an assigned MMW night role including night-branch review, or consult an Advisor for an independent second opinion.
---

# Dispatch

Read this file, then the skill and role reference named in your assignment in your first message. That role is yours for this run. The sender keeps its own. A later result or question does not start you over, and it does not give you the sender's role.

Follow only your assigned role's current step. A linked procedure returns to the step that called it; loading its full document does not start its other branches. To consult an Advisor, use [Consult an Advisor](references/advisor.md), then resume your current task; this starts no Coordinator or night. For an authorized spec or ticket execution with no assigned role, use [Coordinator](references/coordinator.md). The standalone review case below has its own entry condition.

The installed runtime is the runtime of this night. Run its skills and this `dispatch.sh`. A commit that changes those files in the repository does not become the runtime until a later run.

## Runtime

Before the first tool call, resolve this installed skill's runtime through [Resolve the runtime](references/runtime.md). That procedure returns absolute `dispatch` and `labels` paths and the runtime version. Reuse those paths for the rest of this run. A caller that needs only tools follows this section and returns to its own step; it starts no Coordinator or night.

Run `bash DISPATCH ...` from the consuming repository, where DISPATCH is the returned `dispatch` path. The command prints JSON. It does not start the subagent. A later `dispatch.sh` command in an MMW skill means this same resolved path.

For model commands (`show`, `row`, `spawn`) and `board`, pass `--host HOST`. HOST is your current host, `cursor` or `codex`. Both use the same user file `~/.agents/models.json`; the argument selects that host's model rows.

Each object in the printed `cards` array is a card: one assignment for the sender to dispatch. `description` is its task label. Use `model_row` to choose the subagent's model settings, and send `prompt` unchanged as its task. The role in `model_row` names a model configuration row; the prompt says what work to do.

Send each card to a **FRESH AGENT**. A **FRESH AGENT** is a newly created agent with a new context that does not inherit the sender's conversation or reuse another agent's context. Disable conversation inheritance in the host's spawn call. The card's prompt and named sources supply its task context. Wait for its result unless the sending step says to continue other work. `skipped` names a role that does not run; continue the step without it.

Read another role's model row with `dispatch.sh row ROLE --host HOST`. `inherit` keeps the sender's model setting for that field; it does not inherit conversation context.

`dispatch.sh spawn researcher --prompt FILE --host HOST` uses the researcher model row and copies the file's full text into the assignment's prompt. The sending skill supplies the task, the context and sources needed without the parent conversation, the scope, and what to return. This model row does not require the subagent to use the research skill.

`dispatch.sh spawn advisor --prompt FILE --host HOST` uses the advisor model row and copies the complete assignment unchanged. The caller uses [Consult an Advisor](references/advisor.md) to prepare the brief and handle the answer. The assigned agent follows the **advisor** skill.

Return the result the reference names, with the evidence it names. Send non-blocking findings promptly and continue your task. A blocking question returns to the sender and ends the turn; continue the same subagent with the answer. A returned result continues the step that sent it, from the action that step was waiting on. A missing or incomplete result is a limitation of that step, not a success.

When no assigned role is named and the request is to review a branch, a PR, or since a commit, stop. The only review is the Coordinator's night-branch review, and it runs once from that step. It reviews the night branch, not the named PR. If this checkout is not a night branch, say that.
