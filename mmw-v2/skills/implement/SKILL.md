---
name: implement
description: "Implement a piece of work based on a spec or set of tickets. Dispatches a headless Codex worker per ticket inside the task worktree, verifies each report against the code, then runs /code-review over the whole change."
disable-model-invocation: true
---

# Implement

Build the work described by the spec and its tickets. The spec is settled and the seams are agreed; this skill executes that plan rather than reopening it.

**You do not write the code.** Each ticket goes to a headless Codex worker. That isn't a preference — `docs/agents/models.md` keeps the main thread from becoming the author of the code, because an author has no standing to judge findings about it. Your job here is to prepare the work, dispatch it, verify what comes back, and drive the review.

## Process

### 1. Confirm the ground

Four things must hold. If any doesn't, stop and say which.

| Check | How | If it fails |
| --- | --- | --- |
| You're in the task worktree | `git rev-parse --show-toplevel` ends in `.worktrees/<slug>` | Create or enter it per `docs/agents/worktrees.md` |
| The spec is here | `docs/specs/<slug>/` exists on this branch | Run `/to-spec` first |
| The spec names its seams | read it | Go back to `/to-spec` step 2 — a worker cannot agree seams with the user |
| Tickets exist | per `docs/agents/issue-tracker.md` | Run `/to-tickets` first |

### 2. Take the next ticket

Work the **frontier**: tickets whose blockers are all closed, with no assignee, labelled `ready-for-agent`. Take them in the order `to-tickets` published. Claim the one you're starting — that's the first write on the ticket, and it's what stops two runs colliding.

One ticket at a time in this worktree. If the frontier is genuinely wide and the user wants tickets built in parallel, fork a worktree per ticket off this branch (`docs/agents/worktrees.md`) — never two workers on one worktree.

### 3. Assemble the worker prompt

From files, not from memory:

1. `worker-brief.md` next to this file, in full.
2. The TDD discipline in full — `tdd/SKILL.md`, `tdd/tests.md`, `tdd/mocking.md`, `tdd/quality-bar.md`.
3. The spec's path in this worktree, and its seam list quoted.
4. The ticket: its title, what to build, and every acceptance criterion, pasted in. Paste it even when the tracker is reachable — a worker that has to go and fetch its own ticket can fetch the wrong one, and the prompt is then no longer the record of what you asked for.

Write it to `.dispatch/<slug>-<ticket>.prompt.md` (`mkdir -p .dispatch`). Never hand a worker a path inside this plugin — it can't read it and will invent something instead.

### 4. Dispatch

Follow `dispatching-agents`. Writable sandbox, and the working tree must be clean before the first dispatch or you won't be able to tell the worker's diff from your own. Take the model from `docs/agents/models.md` — the high-risk tier when the ticket touches billing, permissions, or a data migration. That call is yours, not the worker's.

### 5. Verify what comes back

Per `judging-agent-output`, a completion report is evidence, not a conclusion. Before you accept it,

- re-run the tests it says it ran, and read what they print;
- read the diff it produced;
- confirm the commit exists and references the ticket.

A report that says done while a test fails is a failed run, not a finished ticket. Send it back with what you saw, resuming the same worker session — it still holds the context.

If the worker stopped instead, read its attempt history before doing anything else. A worker blocked on a conflict between the ticket and the code is telling you something about the spec, not about itself; that goes to the user, not to a second worker.

Once it's verified, close the ticket and take the next one.

### 6. Review the whole change

When every ticket is closed, run `/code-review` over the spec's whole diff, with the branch point as the fixed point. Not per ticket — the review is looking for what one ticket did to another, and that is invisible from inside a single ticket.

Accepted findings go back out to a fresh worker as a fix ticket, carrying the `file:line` and what needs to change. Then re-review per `/code-review` step 7, which only looks at the fixes and what they touched.

### 7. Hand back

Report to the user in business terms: what now works, what proves it, what was shelved and where it went. The branch is ready to merge; merging it, and clearing up the worktree, is theirs to approve.

## Why the worker commits per ticket, not once at the end

Matt's original reviews first and commits at the end. Here the commit comes per ticket, because the worker is a separate process that can stop halfway: an uncommitted worktree would lose the finished tickets along with the stuck one. Committing per ticket also gives you the boundary step 5 needs — one ticket, one diff, one thing to verify. The review still happens before anything merges anywhere.
