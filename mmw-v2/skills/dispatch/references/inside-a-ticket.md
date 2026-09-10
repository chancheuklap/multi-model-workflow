# Inside a ticket

You are the worker on ticket `<n>`. From here you start the two agents that judge your work, and read what became of one you started when its wake arrives. Resolve `<dispatch>` and `<engine>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md); what `start` does and how a wake reaches you are in that same file.

| You want to | Run |
| --- | --- |
| Work a ticket you picked up yourself, with no `start` behind you | `<dispatch> adopt <n>`, from the ticket's worktree on `issue-<n>`, before you claim it: without a `worker.started` naming your session, your reviewer's report would wake nobody and `start <n> reviewer` would refuse |
| Start the reviewer on your ticket | `<dispatch> start <n> reviewer`, then end your turn. You are woken with `#<n> reviewer.reported` once its report is on the ticket: read the report, the comment on the ticket that carries that event, then `<dispatch> ack <n> reviewer.reported` |
| Start the verifier on your ticket | `<dispatch> start <n> verifier`, then end your turn. Start it once. You are woken with `#<n> verifier.passed` or `#<n> verifier.failed`: read the verdict — `<dispatch> wait <n> verifier` prints it with the commit it covers and, on a failure, the criteria it failed — then `<dispatch> ack <n> <that event>` |
| Read a result event on your ticket in one line | `<dispatch> wait <n> worker\|reviewer\|verifier`: prints the newest result event of that kind by name and key fields (`ticket.passed` / `ticket.returned`, `reviewer.reported base=… head=…`, `verifier.passed commit=…` / `verifier.failed commit=… failed=…`), reading the ticket before it waits at all |

The `wait` and `ack` rows and their exit codes are also what the main agent of a night reads: the commands are the same ones, whichever session runs them.

## Exit codes

**`start <n> reviewer|verifier`:**

| Code | What happened |
| --- | --- |
| `0` | The session is running; its id is on stdout and its `reviewer.started` or `verifier.started` event is on the ticket |
| `2` | Nothing was started — or a session was started and stopped again because its start event could not be written, so no command could have found it. The reason is on stderr — read it verbatim. Typical causes: the ticket is not `OPEN` / not `ready-for-agent` / still blocked; no running relay watches the ticket, so its result would wake nobody; no live-table row for that agent; no recorded base commit (reviewer); the runner refused the start (its reason is on stderr, and it was not retried); the tracker would not take the start event; an argument this form does not take. A 2 here is a pipeline fault: `<engine> <n> --sub-issue fault <file>`, where the file's body is the command you ran and the output you saw, then stop |

**`ack <n> <event>`**, or **`ack relay.recovered`:** `0` that wake is acked — the relay removes it, and every earlier wake it sent this session, from the wake queue; `2` nothing was acked: this session cannot name itself (its runner's reason is on stderr), or no wake with that ticket and event is queued for this session — acked already, sent to another session, or never queued — and stderr lists the wakes that are queued for it (check the number and the event name against the wake you read).

**`adopt <n>`**, for a session that picked ticket `<n>` up itself rather than being started on it: run from the ticket's worktree on branch `issue-<n>`, before claiming. `0` this session is the ticket's worker: a `worker.started` event names its runner and session with the ticket's grade row, this worktree, its branch and base, and a relay watches the ticket — the night's, or one started for this ticket with this session as the one woken; stdout is the session id. It takes no slot on the product: the first criteria run that needs the product claims one. Adopting again from the same session writes nothing more. `2` nothing was adopted, the reason on stderr: this session cannot name itself; the ticket is not open, not `ready-for-agent` or still blocked; this checkout is not on `issue-<n>`; another live worker holds the ticket; no relay could be had; or the tracker would not take the event.

**`wait <n> worker|reviewer|verifier`:** `0` the result event is on the ticket and its name and key fields are on stdout; `1` the agent is gone — `closed`, `error`, or no longer listed — and no result event exists; stderr names the next step. An `idle` agent is not gone: an agent that has handed work to subagents and ended its turn sits at `idle` for the whole of that work, doing exactly what it was told, and `3` is the answer; `2` the ticket has no `<kind>.started` event, its comments could not be read, or one of them carries an event block nobody can read (stderr names the comment); `3` no result yet and the agent is still working, which covers `running`, `initializing` and `idle`. It reads the ticket before it waits at all, so a result already there returns at once, which is the case after a wake. Otherwise it spends at least `MMW_WAIT_S` seconds (default 90) before answering `3`, re-reading the ticket every `MMW_WAIT_BEAT_S` seconds (default 10). It writes nothing. A `3` is not a reason to run it again: end your turn, and the wake comes when the result lands.
