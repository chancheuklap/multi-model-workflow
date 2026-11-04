---
name: dispatch
description: Coordinate an authorized spec or one ticket, carry out the assigned night role, or review a branch, a PR, or since a commit.
---

# Dispatch

Read this file, then the one reference for the assigned role in your first message. That role is yours for this run. The sender keeps its own. A later result or question does not start you over, and it does not give you the sender's role.

The installed runtime is the runtime of this night. Run its skills and this `dispatch.sh`. A commit that changes those files in the repository does not become the runtime until a later run.

Resolve `../../tools/dispatch/scripts/dispatch.sh` from this file to an absolute path, and run it in the consuming repository. The command prints JSON. It does not start the subagent.

When that JSON contains `cards`, hand each object to Task as printed. Each object is already the Task arguments; pass those fields through as they stand. Wait, unless the object has `run_in_background` set. `skipped` names a card that was not printed. That role does not run, and the step continues without it. On Codex, hand the same object to the host's subagent tool. The object already carries the fields that host uses.

Return the result the reference names, with the evidence it names. A question returns to the sender and ends the turn. The sender answers by resuming that same Agent ID. On Cursor, that is Task with `resume` set to the Agent ID. A returned result continues the step that sent it, from the action that step was waiting on. A missing or incomplete result is a limitation of that step, not a success.

When no assigned role is named and the request is to review a branch, a PR, or since a commit, stop. The only review is the Coordinator's night-branch review, and it runs once from that step. It reviews the night branch, not the named PR. If this checkout is not a night branch, say that.
