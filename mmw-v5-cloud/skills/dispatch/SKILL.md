---
name: dispatch
description: Coordinate an authorized spec or one ticket using cloud agents, carry out an assigned cloud Worker task, or dispatch native cloud subagents for a current working method.
---

# Dispatch

## Enter with your assignment

Use your assigned role and scope. Coordinating an authorized Spec or one ticket uses [Coordinator](references/coordinator.md); an assigned `worker` uses [Worker](references/worker.md). These references supply ordered work and call the common methods below.

An agent borrowing dispatch keeps its current role and working method. Assigned Standards, Spec and Tests reviewers enter `code-review` and their assigned axis reference. Researcher, advisor and candidate assignments follow their supplied brief and method. A result or follow-up continues the same task, rather than restarting its workflow.

## Use the installed runtime

Use the project-installed MMW runtime and `.agents/models.json` fixed by this night's starting commit. Resolve skill and tool paths from that installation in your own checkout. Run repository commands from the consuming checkout.

From this skill directory, `../../tools/dispatch/scripts/dispatch.sh` supplies `status`, `land` and `board`; `../../tools/dispatch/scripts/models.py` reads project model settings. Use their absolute paths. Ordinary branch operations use Git. The runtime and model configuration stay fixed for this run while product code advances.

Read this run's full configuration with `python3 MODELS show --at RUNTIME_COMMIT`, or one role with `python3 MODELS row ROLE HOST --at RUNTIME_COMMIT`; for review axes use ROLE `review-axis`. RUNTIME_COMMIT is the existing starting commit of this run, supplied in the assignment; reading its Git version keeps board edits for the next run. HOST is the actual native host, such as `codex` or `cursor`. Pass returned non-`inherit` settings to the native tool when it supports them. A configured model or host does not create a tool capability; report an unsupported choice rather than launching another CLI or silently selecting a replacement model.

## Prepare an assignment

Give each subagent a self-contained assignment: task and source material, scope, working method, code version when relevant, and expected result. Supply required Issue bodies and relevant comments as content, not only GitHub links.

Use the kickoff template supplied by the current working method when it has one; otherwise provide the complete assignment described here. The Coordinator's Worker template is in its reference; axis assignments are defined by `code-review`. Use this run's project model settings.

## Start a subagent

Use this host's actual native cloud-agent tools to send the assignment and supported settings. Workers and assistance tasks execute in the cloud; review axes execute in the Worker's cloud environment or assigned isolated copies. Retain the native reference for subsequent conversation. The native tool establishes the parent-child relationship; there is no separate registration command.

## Talk, wait and continue

Use the native parent-child channel for questions, results and follow-ups to the same agent. Read the actual returned evidence before continuing the role step that dispatched it. Wait using the host's supported mechanism; a missing or failed response remains unresolved. Preserve valid work and send precise corrections to the original agent.

## Return a usable result

Return the actual result and evidence to the assigned recipient, including relevant commits and limitations. Report problems, their evidence, blocking effect and requested action directly to the parent.

The local Coordinator handles the workflow's GitHub records. Cloud agents need Git access for their assigned branches, not `gh` or Issue/PR API access. The Coordinator preserves original reports, decisions and results as ordinary records; native conversation delivers the handoff. Its role reference defines when to record each result. Root Coordinators deliver their result to the owner.

## Read command outcomes before retrying

Read the result of a tool or command before repeating an action. Inspect what it already changed and preserve unresolved failures in the result. Each role's reference identifies the operations that role performs.
