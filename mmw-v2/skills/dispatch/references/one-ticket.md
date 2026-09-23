# One ticket, outside a night

You are starting one worker on one ticket, with no batch behind it. A ticket outside a night belongs to no spec, so no `advance` will ever collect it: `land <n>` is its whole ending. Resolve `<dispatch>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md); how a wake reaches you is in [how-it-works.md](how-it-works.md), and what you do on one is `## On waking` in [../SKILL.md](../SKILL.md).

Four steps:

1. `<dispatch> open-ticket <n>`: it opens a watch on ticket `<n>` alone with this session as its main agent — the runner and session its runner's adapter reads from this process — and starts the relay when none runs for this repository. It also registers and starts this repository's task board, the one view of the ticket for a person, and prints its URL: hand it to the user. A night open on this repository keeps its own watch and its own main agent.
2. `<dispatch> start <n> worker`, from the checkout branch this ticket will merge into. That branch must exist on origin; `start` fetches it, records it as `worker.started.into`, creates the ticket branch from `origin/<branch>` and pushes the new ticket branch before the worker runs. Then end your turn.
3. You are woken with `#<n> ticket.passed` or `#<n> ticket.returned`, or with one of the four below. Read that event on the ticket and `<dispatch> ack <n> <that event>` (exit codes under `## On waking` in [../SKILL.md](../SKILL.md)), then act on it.
   - `#<n> worker.lost`: the worker's session stopped. `<dispatch> start <n> worker` starts another in the same workspace; it first commits tracked edits and pushes the ticket branch to origin.
   - `#<n> ticket.refused`: the worker refused to claim the ticket, and the event's `reason` says why. Fix that, then `<dispatch> start <n> worker` again.
   - `#<n> child.opened`: a `fault` stopped the worker — fix what the child names, then `<dispatch> resume <n> "<what you fixed>, then: continue"`; a `decision` is for the user, and the worker carries on.
   - `#<n> child.opened` of kind `contract`, a `watchdog:` line, or an `MMW turn guard:` line: act as [night.md](night.md) under **3. Each time something wakes you** says for it, reading `python3 <events.py> fold <n>` where it says `status`. A `watchdog:` or `MMW turn guard:` line is not acked.
4. Once the ticket passed or came back, run `<dispatch> land <n>` from any checkout of this repository; what it does is under [Exit codes](#exit-codes) below.

## Exit codes

**`open-ticket <n>`:**

| Code | What happened |
| --- | --- |
| `0` | A watch on `<n>` is open with this session as its main agent, and a relay runs; stdout reads `opened #<n>: wake-ups go to <runner> session <session>; task board <url>`, and stderr says whether the watch was opened now or was open already, and whether the relay was started or found running. A task board that would not start leaves the `; task board <url>` part off stdout and says why in one stderr line; the watch is open all the same, and `<dispatch> board` starts the board once that reason is fixed |
| `2` | Nothing was opened. The reason is on stderr; read it verbatim. Every open watch is left as it was |

**`start <n> worker`:**

| Code | What happened |
| --- | --- |
| `0` | The session is running; its id is on stdout and its `worker.started` event is on the ticket |
| `2` | Nothing was started. The reason is on stderr; read it verbatim |

**`land <n>`:**

It reads `into` and `ticket.passed.commit` from the ticket, merges and checks in the detached merge worktree, fast-forward pushes `origin/<into>`, gives back the claim and slot, archives the workspace, records `ticket.landed`, and closes the watch. It deletes the ticket branch locally and on origin only when no worktree uses it and each copy is contained in `origin/<into>`; an unlanded copy is kept, and a deletion failure does not undo the landing. A conflict or red check writes `ticket.bounced` and leaves the workspace and ticket branch standing. When the ticket belongs to an open night, the first bounce since `spec.opened` returns it to `ready-for-agent` for the next `advance`, and the second leaves it in `needs-triage`; without an open night, `land` leaves it in `needs-triage`. The one-ticket watch closes.

| Code | What happened |
| --- | --- |
| `0` | Done, already present, or recorded as `ticket.bounced`; stderr carries `land: merged <m>, already in <a>, bounced <b>, still working <w>, already landed <d>, failed <f>` |
| `1` | Something was left standing: a ticket closed without `ticket.passed` has work outside `origin/<into>`, a landing could not finish, or the relay did not end; stderr names it |
| `2` | Nothing was touched: not a git repository, an unreadable ticket, a missing remote base, or invalid arguments |
