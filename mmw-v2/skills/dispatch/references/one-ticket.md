# One ticket, outside a night

You are starting one worker on one ticket, with no batch behind it. A ticket outside a night belongs to no spec, so no `advance` will ever collect it: `land <n>` is its whole ending. Resolve `<dispatch>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md); how a wake reaches you, and what you do on one, are in that same file.

Four steps:

1. `<dispatch> open-ticket <n>`: it opens a watch on ticket `<n>` alone with this session as its main agent — the runner and session its runner's adapter reads from this process — and starts the relay when none runs for this repository. A night open on this repository keeps its own watch and its own main agent.
2. `<dispatch> start <n> worker`, then end your turn.
3. You are woken with `#<n> ticket.passed` or `#<n> ticket.returned`, or with one of the three below. Read that event on the ticket, act on it, then `<dispatch> ack <n> <that event>` (exit codes in [inside-a-ticket.md](inside-a-ticket.md)).
   - `#<n> worker.lost`: the worker's session stopped. `<dispatch> start <n> worker` starts another in the same workspace; it first commits what the lost one left uncommitted on the ticket branch.
   - `#<n> ticket.refused`: the worker refused to claim the ticket, and the event's `reason` says why. Fix that, then `<dispatch> start <n> worker` again.
   - `#<n> child.opened`: a `fault` stopped the worker — fix what the child names, then `<dispatch> resume <n> "<what you fixed>, then: continue"`; a `decision` is for the user in the morning, and the worker carries on.
4. Once the ticket passed or came back: `<dispatch> land <n>`, run in the checkout of the branch it merges into. It merges the ticket's branch, gives its claim back, runs the product's `stop` in the ticket's worktree and gives its slot back, stops every session the ticket's `*.started` events name, removes its worktree, records `ticket.landed` on the ticket, and closes the watch `open-ticket` opened; the relay ends with it when it watched nothing else.

## Exit codes

**`open-ticket <n>`:**

| Code | What happened |
| --- | --- |
| `0` | A watch on `<n>` is open with this session as its main agent, and a relay runs; stdout reads `opened #<n>: wake-ups go to <runner> session <session>`, and stderr says whether the watch was opened now or was open already, and whether the relay was started or found running |
| `2` | Nothing was opened. The reason is on stderr — read it verbatim. Typical causes: this session runs in no runner whose adapter can read its id (run it inside a session of one), or its runner shows that session stopped; the ticket is already watched by a night's watch on its spec — it is that night's ticket, and its wakes go to that night's main agent; the board could not be read to check that; the relay exited as it started (its log's last lines are on stderr). Every open watch is left as it was |

**`start <n> worker`:**

| Code | What happened |
| --- | --- |
| `0` | The session is running; its id is on stdout and its `worker.started` event is on the ticket |
| `2` | Nothing was started. The reason is on stderr — read it verbatim. Typical causes: the ticket is not `OPEN` / not `ready-for-agent` / still blocked (a blocker that passed holds until it has landed); no running relay watches the ticket (step 1 was not run); two worker-grade labels; no live-table row for that agent; the runner refused the start (its reason is on stderr, and it was not retried); an argument this form does not take |

**`land <n>`:**

| Code | What happened |
| --- | --- |
| `0` | Done. Stderr carries the merge line and the tally `land: merged <m>, archived <a>, released <r>, still working <w>, left unmerged <u>`. A ticket still being worked is named on stderr, nothing is done to it, and its relay keeps running. A ticket whose product would not go down keeps its workspace and is named there too — archiving deletes the worktree the `stop` command lives in, so that one is left recoverable |
| `1` | Something was left standing, and stderr names it: the ticket closed without a `ticket.passed` and its branch is not in `HEAD` — archiving deletes the worktree, so this one waits for you: merge that branch, or decide the work is abandoned and archive it yourself — or the relay watching the ticket did not end, and stderr names its pid |
| `2` | Nothing was touched: not a git repository, uncommitted tracked changes, or a ticket number that is not digits |
| `3` | A merge is in conflict and is still in the tree. Resolve it with the `resolving-merge-conflicts` skill, run this repository's checks, commit the merge, then run `land` again |
