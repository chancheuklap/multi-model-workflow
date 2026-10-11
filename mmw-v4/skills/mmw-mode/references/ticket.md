# Ticket template

The body of each GitHub issue the To tickets playbook (`../playbooks/to-tickets.md`) publishes, and of each ticket a playbook opens outside any spec: Bug fix, Perf issue, Hillclimb, Feature, Refactoring, Visual parity, and Authoring or modifying a skill. Replace each section's guidance with the content.

<issue-template>

## Problem

Only on a ticket a playbook opens outside any spec. Its first line is `Playbook: <the playbook it needs>`, by the title on that playbook's route line. Then what was seen, where, and by whom, with the owner's words quoted as they said them. Written when the ticket is opened, and never edited after, but for a `Playbook:` line not yet known then, which is written once when it is.

## Parent

A reference to the parent spec on the tracker, followed by the numbered Implementation Decisions sections this ticket implements (for example, "#12, Implementation Decisions sections 5 and 7"). The first issue here is read as the ticket's spec. A ticket a playbook opens outside any spec writes "None".

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not layer-by-layer implementation. Write it as numbered points, one thing per point, each point complete with the test that decides it and the reason it is there. A person scans it for the one point they came for, an agent works from it with none of your context, and neither gets through one long paragraph. A choice the user settled in the quiz of To tickets step 7 is a point of its own here, stated as the ticket's decision.

## Read first

The source material behind the sections named under **Parent**: decision tickets, ADRs, research files, prototype directories, domain docs, the sections of `CODING_STANDARDS.md` and `TESTING.md` the spec relies on, copied from what those sections cite, one per line, each with a word on what it settles. The implementer reads these and nothing else from the spec's Sources. Whatever here records a settled conclusion (the chosen artifact of a prototype, the decision an ADR states in the paragraph under its title, the resolution of a decision ticket) is a **baseline**: a contract, not a reference, marked as one on its line. Write "None" if the sections cite nothing.

## Seam

Where this ticket is verified: the test layer and directory from the spec's Testing Decisions, and the precedent to copy. Then, from the same section's **How a test arrives at a state**, what puts the system into the states the criteria below name; when this ticket is the one that builds that, say so here as well as under **Owns**.

## Owns

The repository-relative paths this ticket may write, one per line, the test directory or test file from **Seam** included. Mark what this ticket creates with "(new)". A file this ticket must edit to put what it creates in service (the registry, router, stylesheet, parent template or index that has to name it) belongs here as well, though another ticket created it: this section says where this ticket may write, not where its own code lives. No absolute path, no `..`, no bare `**`. Match the granularity to the split: a directory glob where this ticket owns the directory alone, file paths where several tickets divide one directory. Two tickets that can run at the same time must not overlap here; where they cannot be pulled apart because both must edit one file, add a **Blocked by** edge instead. Everything outside these paths is read-only for this ticket. A change a ticket needs in a tool skill outside the repository is not an entry here: the toolbox is improved in use, and the change is made there at once.

A ticket that deletes or renames a file, a script, a contract field, or a criterion word takes every place `grep` finds that name into its own **Owns**. Find those places by grepping the name, not by listing from memory. When a hit is only a stale reference another ticket already owns, leave it off this ticket and open a ticket **Blocked by** that other ticket.

- src/import/**
- tests/import/**
- src/import/ui/** (new)

## Acceptance criteria

- [ ] AC1: <what must be true, in the spec's exact values>
  CHECK: <the command that decides it>
  EXPECT: <the line only a passing run prints>
  EVIDENCE: pending
- [ ] AC2: <the next thing that must be true>
  CHECK: <the command that decides it>
  EXPECT: <the line only a passing run prints>
  EVIDENCE: pending

</issue-template>

## Opening a ticket

A playbook outside any spec opens its ticket at its first step, before the plan is known:

1. Write the body with `## Problem` alone, then `gh issue create --title "<what is wrong or wanted, in a few words>" --label mmw:ticket --body-file <file>`. `mmw:ticket` is its only label: `verify-ticket.py --lint` passes it, no worker can claim it without `ready-for-agent`, and no `advance` reaches it, since it sits under no spec.
2. From a checkout of the project branch, `git fetch origin`, then `git worktree add .worktrees/fix-<n> -b fix-<n> origin/<project branch>` and `git -C .worktrees/fix-<n> push -u origin fix-<n>`. When `fix-<n>` already exists, use it.

Every later step of the playbook works in `.worktrees/fix-<n>`. What it writes there, a reproduction, a harness, a baseline, a decision log, a sketch, a prototype, a glossary entry or an ADR, it commits and pushes on `fix-<n>`; the change itself is written only by the worker. To fill the plan in, write every section below `## Problem` into the body, `## Problem` copied unchanged and `None` under `## Parent`, and run `gh issue edit <n> --body-file <file>`.

A problem nobody is working on now, one a session ran into while doing something else, gets step 1 only and the label `needs-triage`; its `Playbook:` line is written when the kind is plain, and otherwise when the owner picks it. Its `fix-<n>` is opened when the owner picks it, at that playbook's first step.

An issue someone else opened, or a child of a night's ticket, is not worked as it stands: open a ticket of our own whose `## Problem` quotes it with its link, and leave the original as it is. Opening a PR closes it once the pull request merges.

## Handing it back

The last step of every playbook that opens a ticket. Tell the owner what that playbook's `**Reply:**` line names: the problem, its cause or its baseline, the plan, the criteria, and what the ticket leaves out. Then wait for their word.

- **Change it.** Edit the ticket, and hand it back again.
- **Not yet.** `gh issue edit <n> --add-label needs-triage`.
- **No.** `gh issue edit <n> --add-label wontfix`, then `gh issue close <n> --reason "not planned"`.
- **Go.** Run One ticket (`../playbooks/one-ticket.md`) on it.
- **Too big for one ticket.** Run To spec (`../playbooks/to-spec.md`), then close the ticket with a comment linking the spec. `fix-<n>` stays.

A criterion may carry a fifth line, `TIMEOUT: <seconds>`, when its `CHECK:` needs longer than the 600 seconds every `CHECK:` gets by default. The largest `TIMEOUT:` on a ticket applies to all its criteria, in every run. A `CHECK:` runs with `$MMW_TICKET` set to the ticket's number and, once a worker has started on the ticket, `$MMW_BASE_REF` set to `origin/<the branch the ticket merges into>`, so a command can name either without writing it in.

Avoid implementation file paths or code snippets: they go stale fast; paths to source material stay, and so do the two kinds of path a ticket cannot do without: the test directory or test file under **Seam**, and the paths under **Owns**, which say where this ticket may write, not where its code lives. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.
