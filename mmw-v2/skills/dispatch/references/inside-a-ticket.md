# Inside a ticket

You are the worker on ticket `<n>`. From here you start the two agents that judge your work, and read what became of one you started when its wake arrives. Resolve `<dispatch>` and `<engine>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md); what `start` does and how a wake reaches you are in that same file.

| You want to | Run |
| --- | --- |
| Work a ticket you picked up yourself, with no `start` behind you | Run `<dispatch> adopt <n>` before you claim it; its full contract is under [Exit codes](#exit-codes) below |
| Bring in tickets that landed on your base branch while you worked | `<dispatch> integrate <n>`, from the ticket's worktree on `issue-<n>`, before running your criteria. Exit 0 merged `origin/<base branch>` or it was already contained; a clean merge names the tickets it brought in. Exit 2 changed nothing: stderr names a dirty tracked tree, the wrong branch, missing or unreadable `worker.started.into`, a missing `origin/<base branch>` or a merge that could not start. Exit 3 leaves the merge in conflict and reports those ticket numbers and titles plus the conflicted files; use the `resolving-merge-conflicts` skill, run the affected repository checks, commit that merge, then run `<dispatch> integrate <n>` again. It never pushes, rebases or aborts |
| Start the reviewer on your ticket | `<dispatch> start <n> reviewer`, then end your turn. You are woken with `#<n> reviewer.reported` once its report is on the ticket: read the report, the comment on the ticket that carries that event, then `<dispatch> ack <n> reviewer.reported` |
| Start the verifier on your ticket | `<dispatch> start <n> verifier`, then end your turn. Start it once. You are woken with `#<n> verifier.passed` or `#<n> verifier.failed`: read the verdict — `<dispatch> wait <n> verifier` prints it with the commit it covers and, on a failure, the criteria it failed — then `<dispatch> ack <n> <that event>` |
| Carry on after `#<n> reviewer.lost` or `#<n> verifier.lost` | The reviewer or verifier you started died before its result landed: its runner said the session stopped, and that event ended its hold. Start another the same way (`<dispatch> start <n> reviewer` or `verifier`), then `<dispatch> ack <n> <that event>` and end your turn |
| Carry on after `#<n> worker.queued` | Follow the `verify-ticket` skill's `references/running-criteria.md` under **A criterion that runs the product** |
| Read a result event on your ticket in one line | `<dispatch> wait <n> worker\|reviewer\|verifier`: prints the newest result event of that kind by name and key fields (`ticket.passed` / `ticket.returned`, `reviewer.reported base=… head=…`, `verifier.passed commit=…` / `verifier.failed commit=… failed=…`). It reads the ticket and nothing else |

The `wait` and `ack` rows and their exit codes are also what the main agent of a night reads: the commands are the same ones, whichever session runs them.

## Exit codes

**`start <n> reviewer|verifier`:**

| Code | What happened |
| --- | --- |
| `0` | The session is running; its id is on stdout and its `reviewer.started` or `verifier.started` event is on the ticket |
| `2` | Nothing was started — or a session was started and stopped again because its start event could not be written, so no command could have found it. The reason is on stderr — read it verbatim. A 2 here is a pipeline fault: `<engine> <n> --sub-issue fault <file>`, where the file's body is the command you ran and the output you saw, then stop |

**`ack <n> <event>`**, or **`ack relay.recovered`:** `0` that wake is acked — the relay removes it, and every earlier wake it sent this session, from the wake queue; `2` nothing was acked: this session cannot name itself (its runner's reason is on stderr), or no wake with that ticket and event is queued for this session — acked already, sent to another session, or never queued — and stderr lists the wakes that are queued for it (check the number and the event name against the wake you read).

**`adopt <n> [--into <branch>]`**, for a session that picked ticket `<n>` up itself rather than being started on it: run from the ticket's worktree on branch `issue-<n>`, before claiming. `into` comes from the latest `worker.started`, else the open night's `spec.opened`, else the required `--into` outside a night; it must exist on origin. `0` this session is the ticket's worker and `worker.started` records its runner, session, grade row, worktree, ticket branch, base branch and base commit; a relay watches the ticket, stdout is the session id, and no product slot is taken. Adopting again from the same session writes nothing more. `2` nothing was adopted; stderr names a session it cannot identify, the ticket state, wrong ticket branch, missing `origin/<base branch>`, `worker.started` without `into`, an existing worker, relay failure or tracker failure.

**`wait <n> worker|reviewer|verifier`:** `0` the result event is on the ticket and its name and key fields are on stdout; `2` the ticket has no `<kind>.started` event, its comments could not be read, or one of them carries an event block nobody can read (stderr names the comment); `3` the ticket carries no result of that kind yet. It reads the ticket once and answers: it waits for nothing, asks no runner and writes nothing. A `3` is not a reason to run it again: end your turn, and the wake comes when the result lands; a session that died before its result is the watchdog's to find, and its `reviewer.lost` or `verifier.lost` wakes you instead.
