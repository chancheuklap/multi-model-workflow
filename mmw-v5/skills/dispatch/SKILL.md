---
name: dispatch
description: Coordinate an authorized spec or one ticket, send an independent agent session, or carry out an assignment sent by dispatch. Use when dispatching, receiving the assigned role, or continuing the assigned task.
---

# Dispatch

## Understand your assignment

On first entry, read this file in full. Use the role assigned to you, not the sender's role. Read the additional task files named in your first message; they supply the particular task. Keep the ticket, source decisions and assigned scope authoritative.

| Your assignment | Working sequence |
| --- | --- |
| Coordinate an authorized spec or one ticket, or continue its results | [Coordinator](references/coordinator.md) |
| Assigned role `worker` | [Worker](references/worker.md) |
| Assigned role `reviewer` | [Reviewer](references/reviewer.md) |
| Assigned role `researcher`, `advisor` or `candidate`, with a brief | [Brief assignment](references/brief.md) |

The reference supplies your ordered work. Its steps point back to the common operations below. Sending another task or receiving a notification does not change your role or restart your workflow. An agent borrowing dispatch for its current method uses the common operations and then returns to that method.

Native axis reviewers inside `code-review` follow their assigned review references. Send below starts independent sessions, not native subagents.

## Use this run's tools

Run commands from the consuming repository's checkout, not the skill directory. Resolve the following paths from this skill's directory and use their absolute paths:

| Name used below | Path relative to this skill's directory |
| --- | --- |
| `dispatch.sh` | `../../tools/dispatch/scripts/dispatch.sh` |
| `models.py` | `../../tools/dispatch/scripts/models.py` |
| `verify-ticket.py` | `../../tools/verify-ticket/scripts/verify-ticket.py` |
| `events.py` | `../../tools/verify-ticket/scripts/events.py` |

Use skills and tools from this installation. Keep this runtime, its model configuration and its working instructions fixed for the run; changing the product under review does not change the tools controlling it.

Use the supplied `MMW_HOME` and command environment.

Before running dispatch commands, query `python3 models.py executor`. An empty answer uses the host's usual shell tool. A returned file is the calling runner's tool executor: read and evaluate it in the current host's tool runtime, then call the returned function with the tool bindings, shell command and optional `{cwd}`. Use its `exitCode` and `output` as the command result.

The scripts choose the configured host, model, effort and runner. For a ticket, the worker grade selects the worker row; reviewer uses its own row. `python3 models.py subagent ROW HOST` returns settings for native subagents, not a new independent session. Pass returned non-`inherit` model and effort values to the host's subagent call.

## Prepare an assignment

Name the outcome, scope, sources, working method, verification and expected answer so the assigned agent needs none of your conversation. Include the code version when relevant.

## Send an independent session

A ticket sender uses `dispatch.sh send worker|reviewer N --task FILE`. The script supplies the recipient's role, ticket, comparison and report command and directs it into this dispatch skill. Use this `SKILL.md` as FILE for the automatic ticket workflow; when the caller supplies an additional assignment file, pass that file instead. The recipient reads that file as additional input after this entry. A sender starting a worker outside an open watch must also supply the authorized target as `--into BASE`.

For a brief, the sender [prepares the assignment](#prepare-an-assignment), writes it to a file and uses `dispatch.sh send ROLE [--cwd DIR] [--follow METHOD_FILE] BRIEF_FILE...`. Each file starts one independent session. A method file supplies the assigned method; do not duplicate it into the brief.

## Wait and continue

Do not interrupt dispatched agents or repeat their work. Read the actual returned evidence before continuing the role step that dispatched it.

After dispatching, end the turn and let the relay wake the original session. For `codex-app`, keep this session waiting through the caller's tool executor with `dispatch.sh wait-wake`. Use this active-wait path for another runner only when it supports the command and cannot reliably resume an ended turn. If the adapter cannot wait, report its reason and end the turn rather than repeatedly querying child progress.

Handle each wake in arrival order, one wake at a time:

1. Read what the notification names. For `reviewer.reported`, `dispatch.sh wait N reviewer` prints the review and its comparison. For a ticket outcome or child, read the full corresponding tracker comment and child. For `brief B done`, `dispatch.sh brief show B` gives each answer's path and state; read all answers.
2. Acknowledge after reading and before long work: `dispatch.sh ack N EVENT`, or `dispatch.sh ack brief B`. A `watchdog:` alert is not acked.
3. Continue the step that sent the work. `wait N reviewer` reads the current result once; it does not wait for one to appear.

A lost or incomplete result is a limitation, not a clean review or a successful task.

Closeout, review and child events notify their existing recipients automatically.

## Return the assigned result

Return the assigned result with its actual evidence and limitations. Preserve the ticket, target and code-version identity supplied in your assignment. The role reference or assigned method specifies the required result and completion condition; a method's answer alone is not a delivered assignment.

State what was done, the checks actually run, what the evidence establishes and what remains.

When the first message or brief supplies a report command, the recipient saves the actual result to a UTF-8 file and executes that command successfully before handing back.

The brief sender reads all answers through the common Wait operation. Answers remain available until `dispatch.sh brief close B`; close the batch when no later step needs them.

## Record and resolve a child

Use the current ticket's native child issues to preserve matters that cannot be settled within its assigned work. The child body is written for a receiver who has seen none of your session. State the problem, evidence, affected requirement, what you tried and what decision or repair is needed.

Choose the first matching kind:

| Question | Kind and receiver |
| --- | --- |
| Is an unavailable environment or broken pipeline preventing work? | `fault`; notifies coordinator. Preserve the command, error and unfinished work. |
| Does a required baseline, spec decision or acceptance requirement fail to hold or contradict another source? | `contract`; notifies coordinator. Cite the actual conflict and what would settle it. |
| Do the sources leave observably different product outcomes open? | `decision`, with the default taken; notifies coordinator and adds `needs-triage`. Take the option the ticket, its baselines and the spec make most likely, record the alternatives and default, and carry on. Keep established decisions and the authorized scope intact. |
| Is a supported defect outside the assigned repair? | `finding`; no immediate notification. Coordinator handles it in the closing pass. |
| Is it an optional product change the task does not require? | `deferred`; adds `needs-triage`, with no immediate notification. |

An implementation mistake within this ticket is repaired here. An internal engineering choice with no unresolved product promise is yours to make and explain. A change necessary for assigned behavior does not become optional because it touches another file.

Write a UTF-8 file with the child's title on the first line and its explanation below, then run `python3 verify-ticket.py N --sub-issue KIND FILE`. The whole file becomes the body. The command adds `mmw:child`, adds `needs-triage` for `decision` and `deferred`, and records the kind in the event; a child has no worker-grade label. If child creation succeeded but its event failed, use the error's `--existing CHILD` retry with the same report; do not create a duplicate.

After deciding a child's disposition, the Coordinator uses `dispatch.sh route N CHILD RESOLUTION --report FILE`:

- `fixed`: the matter was actually repaired. For a repository repair, include `--commit SHA` naming the actual committed repair after its checks and push. For environment-only or tracker-only repairs, state exactly what changed in the report; no unrelated commit is a repair receipt.
- `stale --reason invalid`: the asserted problem did not hold.
- `stale --reason fixed-elsewhere`: it held but was repaired elsewhere.
- `became-ticket --became TARGET`: prepare the actual executable-ticket destination as [Coordinator: Close the remaining findings](references/coordinator.md#4-close-the-remaining-findings) says, then route it. The route reclassifies and links, but does not write the task for you.

Closing a child records its disposition; it does not wake its worker. An unresolved owner choice remains visible in triage and the delivery. Do not route it as repaired. The Worker and Coordinator references specify when to wait, decide, or continue.

## Resume a session

To continue an existing ticket session, its caller uses `dispatch.sh resume N MESSAGE`; for an existing brief answer, use `dispatch.sh resume B/N MESSAGE`. Give the exact correction, its source, any commit to integrate and the work to continue. Use the recorded task identity. A child closure alone does not send this message. Interpret the receipt under [Handle command failures](#handle-command-failures).

## Handle command failures

Read the result of a tool or command before repeating an action. Inspect what it already changed and preserve unresolved failures in the result.

Tracker writes can partially succeed; follow the same-command retry or `--existing` recovery named by the error. A notification can interrupt a command: inspect its receipt and recorded state before repeating it. For `resume`, exit 4 means the message was handed over without a confirmed turn start; do not send it again. Exit 3 means it was not accepted; repair the cause before retrying. Exit 2 names the refusal and does not silently start a replacement.
