---
name: dispatch
description: Dispatch independent agent sessions, work an assignment sent by dispatch, receive their results, or run a spec's automated batch. Use before sending an independent session and when a dispatched session is told to enter its assigned role.
---

# Dispatch

Use the role assigned in the first message, not the role of the agent that sent you. On first entry, read this file in full and follow the matching reference. When returning here for a command or a notification, continue your current task; do not restart its workflow.

| Your assignment | Read and follow |
| --- | --- |
| Coordinate a spec batch, or continue the batch whose notifications this session receives | [Coordinator](references/coordinator.md) |
| Assigned role `worker` | [Worker](references/worker.md) |
| Assigned role `reviewer` | [Reviewer](references/reviewer.md) |
| Assigned role `researcher`, `advisor`, or `candidate`, with a brief | [Brief assignment](references/brief.md) |

A session sending an independent task uses the operations below without changing its own assignment. Native subagents inside `code-review` follow their assigned review references; they are not independent sessions started by this tool.

Read any additional assignment file named in your first message, unless it is this entry itself. It supplies the particular task; your role reference supplies the working sequence. Keep the ticket, source decisions and assigned scope authoritative.

## Use this run's tools

Run commands from the consuming repository's checkout, not the skill directory. Resolve the following paths from this skill's directory and use their absolute paths:

| Name used below | Path relative to this skill's directory |
| --- | --- |
| `dispatch.sh` | `../../tools/dispatch/scripts/dispatch.sh` |
| `models.py` | `../../tools/dispatch/scripts/models.py` |
| `verify-ticket.py` | `../../tools/verify-ticket/scripts/verify-ticket.py` |
| `events.py` | `../../tools/verify-ticket/scripts/events.py` |

References to v5 skills also mean this same v5 directory. Use the supplied `MMW_HOME` and command environment. Keep this runtime and its working instructions fixed for the run; changing the product under review does not change the tools controlling it.

Before running dispatch commands, query `python3 models.py executor`. An empty answer uses the host's usual shell tool. A returned file is the calling runner's tool executor: read and evaluate it in the current host's tool runtime, then call the returned function with the tool bindings, shell command and optional `{cwd}`. Use its `exitCode` and `output` as the command result.

Read a command's refusal before deciding its recovery. Tracker writes can partially succeed; follow the same-command retry or `--existing` recovery named by the error. A notification can interrupt a command: inspect its receipt and recorded state before repeating it. For `resume`, exit 4 means the message was handed over without a confirmed turn start; do not send it again. Exit 3 means it was not accepted; repair the cause before retrying. Exit 2 names the refusal and does not silently start a replacement.

## Send an independent session

For a ticket, use `dispatch.sh send worker|reviewer N --task FILE`. The task entry for the automatic ticket workflow is this `SKILL.md`; the script supplies the role, ticket, comparison and report command. An independent worker without an open batch needs the explicit `--into BASE` target. Use the caller's supplied additional assignment file when there is one.

For a brief, write the actual task to a file and use `dispatch.sh send ROLE [--cwd DIR] [--follow METHOD_FILE] BRIEF_FILE...`. Each file starts one independent session. Name the outcome, scope, sources, verification and expected answer so its reader needs none of your conversation. A method file supplies the assigned method; do not duplicate it into the brief.

The scripts choose the configured host, model, effort and runner. For a ticket, the worker grade selects the worker row; reviewer uses its own row. `python3 models.py subagent ROW HOST` returns settings for native subagents, not a new independent session. Pass returned non-`inherit` model and effort values to the host's subagent call.

## Wait, read and acknowledge

After dispatching, end the turn and let the relay wake the original session. Do not interrupt dispatched sessions or repeat their work. For `codex-app`, keep this session waiting through the caller's tool executor with `dispatch.sh wait-wake`. Use this active-wait path for another runner only when it supports the command and cannot reliably resume an ended turn. If the adapter cannot wait, report its reason and end the turn rather than repeatedly querying child progress.

Handle each wake in arrival order, one wake at a time:

1. Read what the notification names. For `reviewer.reported`, `dispatch.sh wait N reviewer` prints the review and its comparison. For a ticket outcome or child, read the full corresponding tracker comment and child. For `brief B done`, `dispatch.sh brief show B` gives each answer's path and state; read all answers.
2. Acknowledge after reading and before long work: `dispatch.sh ack N EVENT`, or `dispatch.sh ack brief B`. A `watchdog:` alert is not acked.
3. Continue the step that sent the work. `wait N reviewer` reads the current result once; it does not wait for one to appear. A lost or incomplete result is a limitation, not a clean review or a successful task.

Brief answers remain available until `dispatch.sh brief close B`; close the batch when no later step needs them. Closeout, review and child events notify their existing recipients automatically. Closing a child alone does not tell a waiting worker to continue: its coordinator uses `resume N MESSAGE`.

## Return the assigned result

A method's answer is not yet a delivered assignment. When the first message or brief provides a report command, save the actual result to a UTF-8 file and use that command successfully before handing back. Preserve its ticket, target and code-version identity. For worker closeout, explicitly choose `complete` or `incomplete` from the real work and evidence. For review, submit the complete checked report, including limitations. For a brief, submit the answer with its actual evidence and unresolved questions.

State what was done, the checks actually run, what the evidence establishes and what remains.

