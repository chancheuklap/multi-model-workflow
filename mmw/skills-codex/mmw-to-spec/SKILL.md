---
name: mmw-to-spec
description: Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed. Use when the user asks for a spec, or when `$mmw:mmw-grilling`, `$mmw:mmw-prototype`, or `$mmw:mmw-wayfinder` has settled the work.
---

This skill takes the current conversation context and codebase understanding and produces a spec. Do NOT interview the user — just synthesize what you already know.

Settled work is not always in this conversation. If the caller passed a map, a shared-understanding record path, or a prototype README path, read that first. A triaged issue is input, not the spec. If a required decision is missing, write what is missing and where you looked, then stop.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

Check with the user that these seams match their expectations.

3. Write the spec using the template below.

Before the first write:

Confirm where this repo is first. Judge top to bottom; stop at the first row that hits.

| Case | How to tell | What you do |
| --- | --- | --- |
| Not in a git repo | `git rev-parse --is-inside-work-tree` fails | Ask the user for the target repo path. Enter that repo, then judge again |
| In the main checkout | `git rev-parse --path-format=absolute --git-dir` equals `--git-common-dir` | Stop. Ask the user to open a worktree with this host, then start a session there |
| No branch | `git symbolic-ref --quiet --short HEAD` is empty | Run `git switch -c <full task-branch name>`. Use the name this skill or the caller already gave; with none in hand, name it after the work in this repo's own branch-naming shape, and say which name you took |
| Task branch already there | None of the above holds | Use the current branch |


`mmw artifact path spec` prints a path; write the spec there. After writing or editing, run `mmw artifact check`. If it exits non-zero, fix the artifact-ref declarations first.

If writing surfaces a missing decision, write what is missing and where you looked, then stop.

Ask whether to send ① spec review (`$mmw:mmw-review`). Wait. If they say yes, the object is this spec; handle findings as `$mmw:mmw-review` specifies.

Show the spec and ask whether to approve it for publish. Do not commit or publish until they explicitly approve.

Then publish it to the project issue tracker. Apply the `ready-for-agent` triage label - no need for additional triage.

After they approve, commit the spec file. `mmw artifact path scratch --sub outbox/spec-issue-body.md` prints a path; write the issue body there (the spec summary and the spec path), then:

```bash
mmw issue create --title "<spec name>" --body-file <that path> --label ready-for-agent
```

Keep the new issue id. Replace `spec_issue: 0` with that id and commit the backfill.

If the caller passed a triaged issue with an agent brief, `mmw issue set-parent <original number> --parent <spec issue number>`. If that command exits non-zero, stop and leave the original issue open. If it succeeds, `gh issue close <original number>`.

Report the spec path and the spec issue number. Ask: split tickets, or stop here.

<spec-template>

---
slug: <name-segment>
summary: <one sentence of what this spec delivers>
date: <YYYY-MM-DD>
branch: <task-branch name>
spec_issue: 0
artifact_refs: []
---

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

The seams the user confirmed:

| Seam | External behaviour verified | Why this layer |
| --- | --- | --- |

## Contract Boundaries

Keep this section only when the work involves an API, cross-boundary data, a database, a scheduled-job payload, billing, or permissions.

Name each contract so a later plan can cite it without copying fields.

Record the settled owner, provider, consumer, contract shape, version or migration need, and how the contract is verified at the public boundary.

## Out of Scope

A description of the things that are out of scope for this spec.

## Further Notes

Any further notes about the feature.

</spec-template>
