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

Use this installation's MMW runtime and the project's `.cursor/models.json` fixed by this night's starting commit. In Cursor, the runtime is installed in the project's `.cursor/`; in Codex, it is installed as a plugin. `dispatch.sh` supplies `status`, `land` and `board`. Ordinary branch operations use Git.

Read this run's full configuration with `python3 models.py show --at RUNTIME_COMMIT`, or one role with `python3 models.py row ROLE HOST --at RUNTIME_COMMIT`; for review axes use ROLE `review-axis`. RUNTIME_COMMIT is the existing starting commit of this run, supplied in the assignment; reading its Git version keeps board edits for the next run. HOST selects the `codex` or `cursor` group in `rows`, according to the actual native host. On Codex, pass the returned model and effort to its subagent call. On Cursor, pass the returned model unchanged to Task's model argument; it includes the configured effort, context window and fast setting.

A configured model or host does not create a tool capability; report an unsupported choice rather than launching another CLI or silently selecting a replacement model.

## Prepare an assignment

Use the Worker kickoff template in the Coordinator reference when sending a Worker. For review axes, use the assignments defined by **code-review**. Use the task's actual repository, branch, commit and source material in the applicable fields.

Supply required Issue bodies and relevant comments as content, not only GitHub links.

## Send a native cloud agent

In Cursor, start a Cloud Worker with native `Task` and select the cloud environment. Review axes use the native Task calls assigned by **code-review**. Pass this run's configured model and effort through the settings the tool supports. Retain the returned Agent ID with its ticket or review axis.

On another host, use its native cloud dispatch and continuation tools. Report a missing operation or unsupported setting. Cursor's `Task` and `resume` names apply to Cursor; dispatch uses the host's native tools under the existing subscription.

## Wait and continue

Do not interrupt dispatched agents or repeat their work. Read the actual returned evidence before continuing the role step that dispatched it.

In Cursor, read the assigned agent's reply from the `Task` result. To answer its question or continue its work, call `Task` with `resume` set to that original Agent ID. Give the answer or correction, its source, any commit to integrate and the work to continue.

A Task completion notification means that one call returned. Read the returned message to decide whether the agent needs an answer, has finished its assignment, or is handing back unfinished work. Continue a question through the original Agent ID.

A lost or incomplete result is a limitation, not a clean review or a successful task.

## Return the assigned result

Apply **principle-prove-it-works**.

Return the assigned result with its actual evidence and limitations. Preserve the ticket, target and code-version identity supplied in your assignment. The role reference or assigned method specifies the required result and completion condition; a method's answer alone is not a delivered assignment.

Return the result in your final reply to the caller. In Cursor, this reply is the Task result. When you need the caller's answer before proceeding, return the question, the reason work is blocked and what you need from the caller, then end this turn. Continue the same assignment when the caller resumes you with its answer.

State what was done, the checks actually run, what the evidence establishes and what remains.

The Coordinator records implementation, review handling and verification in the ticket PR body. Issues and child issues hold requirements, dependencies and decisions. The role references specify who creates the PR, records a child and merges the output. The Coordinator delivers the authorized output to the owner.

## Handle command failures

Read the result of a tool or command before repeating an action. Inspect what it already changed and preserve unresolved failures in the result.
