# Inside a ticket

You are the worker on ticket `<n>`. From here you start the two agents that judge your work, and ask what became of one you started. Resolve `<dispatch>` and `<engine>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md); what `start` does and how you learn a session is done are in that same file.

| You want to | Run |
| --- | --- |
| Start the reviewer on your ticket | `<dispatch> start <n> reviewer`, then `<dispatch> wait <n> reviewer` until it answers `reviewer.reported`; then read the report, the comment on the ticket that carries that event |
| Start the verifier on your ticket | `<dispatch> start <n> verifier`, then `<dispatch> wait <n> verifier` until it answers `verifier.passed` or `verifier.failed`, with the commit it covers and, on a failure, the criteria it failed. Start it once |
| An agent you started has not answered yet | `<dispatch> wait <n> worker\|reviewer\|verifier`: prints its result event by name and key fields (`ticket.passed` / `ticket.returned`, `reviewer.reported base=… head=…`, `verifier.passed commit=…` / `verifier.failed commit=… failed=…`), reading the ticket before it waits at all |

The `wait` row and its exit codes are also what the main agent of a night reads: the command is the same one, whichever kind of agent it is asked about.

## Exit codes

**`start <n> reviewer|verifier`:**

| Code | What happened |
| --- | --- |
| `0` | The session is running; its id is on stdout and its `reviewer.started` or `verifier.started` event is on the ticket |
| `2` | Nothing was started — or a session was started and stopped again because its start event could not be written, so no command could have found it. The reason is on stderr — read it verbatim. Typical causes: the ticket is not `OPEN` / not `ready-for-agent` / still blocked; no live-table row for that agent; no recorded base commit (reviewer); the runner refused the start (its reason is on stderr, and it was not retried); the tracker would not take the start event; an argument this form does not take. A 2 here is a pipeline fault: `<engine> <n> --sub-issue pipeline <file>`, where the file's body is the command you ran and the output you saw, then stop |

**`wait <n> worker|reviewer|verifier`:** `0` the result event is on the ticket and its name and key fields are on stdout; `1` the agent is gone — `closed`, `error`, or no longer listed — and no result event exists; stderr names the next step. An `idle` agent is not gone: an agent that has handed work to subagents and ended its turn sits at `idle` for the whole of that work, doing exactly what it was told, and `3` is the answer; `2` the ticket has no `<kind>.started` event, its comments could not be read, or one of them carries an event block nobody can read (stderr names the comment); `3` still working, which covers `running`, `initializing` and `idle` — run it again. It reads the ticket before it waits at all, so a result already there returns at once. Otherwise it spends at least `MMW_WAIT_S` seconds (default 90) before answering `3`, re-reading the ticket every `MMW_WAIT_BEAT_S` seconds (default 10) — so `run it again` is a beat rather than a loop with nothing in it. It writes nothing.

No host kills a command that outlasts its shell tool: all of them move it to the background and hand back no exit code, which reads as neither `0` nor `3`. When that happens, run `wait` again — and if this host stops waiting sooner than 90 seconds, set `MMW_WAIT_S` below that bound.
