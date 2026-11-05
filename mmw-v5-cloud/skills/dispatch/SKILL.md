---
name: dispatch
description: Coordinate an authorized spec or one ticket, carry out the assigned night role, or review a branch, a PR, or since a commit.
---

# Dispatch

Read this file, then the skill and role reference named in your assignment in your first message. That role is yours for this run. The sender keeps its own. A later result or question does not start you over, and it does not give you the sender's role.

The installed runtime is the runtime of this night. Run its skills and this `dispatch.sh`. A commit that changes those files in the repository does not become the runtime until a later run.

Resolve `../../tools/dispatch/scripts/dispatch.sh` from this file to an absolute path, and run it in the consuming repository. The command prints JSON. It does not start the subagent.

For model commands (`show`, `row`, `spawn`) and `board`, pass `--host HOST`. HOST is your current host, `cursor` or `codex`. Both use the same `.agents/models.json`; the argument selects that host's model rows.

Each object in the printed `cards` array is a card: one assignment for the sender to dispatch. `description` is its task label. Use `model_row` to choose the subagent's model settings, and send `prompt` unchanged as its task. The role in `model_row` names a model configuration row; the prompt says what work to do.

Send each card's assignment to a fresh subagent. Fresh means a new context without the parent conversation. Wait for its result unless the sending step says to continue other work. `skipped` names a role that does not run; continue the step without it.

Read another role's model row with `dispatch.sh row ROLE --host HOST`. `inherit` keeps the sender's setting for that field.

`dispatch.sh spawn researcher --prompt FILE --host HOST` uses the researcher model row and copies the file's full text into the assignment's prompt. The sending skill supplies the task, the context and sources needed without the parent conversation, the scope, and what to return. This model row does not require the subagent to use the research skill.

Return the result the reference names, with the evidence it names. A question returns to the sender and ends the turn. Continue the same subagent with the answer. A returned result continues the step that sent it, from the action that step was waiting on. A missing or incomplete result is a limitation of that step, not a success.

When no assigned role is named and the request is to review a branch, a PR, or since a commit, stop. The only review is the Coordinator's night-branch review, and it runs once from that step. It reviews the night branch, not the named PR. If this checkout is not a night branch, say that.
