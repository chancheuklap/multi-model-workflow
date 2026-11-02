---
name: dispatch
description: Coordinate an authorized spec or one ticket, dispatch a Cloud Worker or review-axis subagent, or carry out an assigned ticket. Use when starting or continuing this automated workflow.
---

# Dispatch

## Understand your assignment

Apply **principle-baseline-is-the-contract** and **principle-never-block-on-the-human**.

On first entry, read this file in full. Use the role assigned to you, not the sender's role. Read the additional task files named in your first message; they supply the particular task. Keep the ticket, source decisions and assigned scope authoritative.

| Your assignment | Working sequence |
| --- | --- |
| Coordinate an authorized spec or one ticket, or continue its results | [Coordinator](references/coordinator.md) |
| Assigned role `worker` | [Worker](references/worker.md) |

The reference supplies your ordered work. Its steps point back to the common operations below. Sending another task or receiving a notification does not change your role or restart your workflow. An agent borrowing dispatch for its current method uses the common operations and then returns to that method.

Native axis reviewers inside `code-review` follow their assigned review references.

## Use this run's tools

Run commands from the consuming repository's checkout, not the skill directory. Resolve the following paths from this skill's directory and use their absolute paths:

| Name used below | Path relative to this skill's directory |
| --- | --- |
| `dispatch.sh` | `../../tools/dispatch/scripts/dispatch.sh` |
| `models.py` | `../../tools/dispatch/scripts/models.py` |

Use skills and tools from this installation. Keep this runtime, its model configuration and its working instructions fixed for the run; changing the product under review does not change the tools controlling it.

Use the project-installed MMW runtime and `.agents/models.json` fixed by this night's starting commit. `dispatch.sh` supplies `status`, `land` and `board`. Ordinary branch operations use Git.

Read this run's full configuration with `python3 models.py show --at RUNTIME_COMMIT`, or one role with `python3 models.py row ROLE HOST --at RUNTIME_COMMIT`; for review axes use ROLE `review-axis`. RUNTIME_COMMIT is the existing starting commit of this run, supplied in the assignment; reading its Git version keeps board edits for the next run. HOST is the actual native host, such as `codex` or `cursor`. Pass returned non-`inherit` model and effort values to the host's subagent call.

A configured model or host does not create a tool capability; report an unsupported choice rather than launching another CLI or silently selecting a replacement model.

## Prepare an assignment

Use the Worker kickoff template in the Coordinator reference when sending a Worker. For review axes, use the assignments defined by **code-review**. Use the task's actual repository, branch, commit and source material in the applicable fields.

Supply required Issue bodies and relevant comments as content, not only GitHub links.

## Send a native cloud agent

Use this host's actual native cloud-agent tools to send the assignment and supported settings. Workers execute in the cloud; review axes execute in the Worker's cloud environment or assigned isolated copies. Retain the native reference for subsequent conversation. The native tool establishes the parent-child relationship; there is no separate registration command.

## Wait and continue

Do not interrupt dispatched agents or repeat their work. Read the actual returned evidence before continuing the role step that dispatched it.

Use the native parent-child channel for questions, results and follow-ups to the same agent. Wait using the host's supported mechanism. Preserve valid work. Give the exact correction, its source, any commit to integrate and the work to continue.

A lost or incomplete result is a limitation, not a clean review or a successful task.

## Return the assigned result

Apply **principle-prove-it-works**.

Return the assigned result with its actual evidence and limitations. Preserve the ticket, target and code-version identity supplied in your assignment. The role reference or assigned method specifies the required result and completion condition; a method's answer alone is not a delivered assignment.

State what was done, the checks actually run, what the evidence establishes and what remains.

Report problems, their evidence, blocking effect and requested action directly to the parent.

The local Coordinator handles the workflow's GitHub records. Cloud agents need Git access for their assigned branches, not `gh` or Issue/PR API access. The Coordinator preserves original reports, decisions and results as ordinary records; native conversation delivers the handoff. Its role reference defines when to record each result. Root Coordinators deliver their result to the owner.

## Handle command failures

Read the result of a tool or command before repeating an action. Inspect what it already changed and preserve unresolved failures in the result.
