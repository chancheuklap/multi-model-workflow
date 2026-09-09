# Inside a ticket

You are the worker on ticket `<n>`. From here you start the two agents that judge your work, and ask what became of one you started. Resolve `<dispatch>` and `<engine>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md); the `create_agent` call each `start` prints, and the two shapes that wake a session, are in that same file.

| You want to | Run |
| --- | --- |
| Start the reviewer on your ticket | `<dispatch> start <n> reviewer`, then the one `create_agent` path in [../SKILL.md](../SKILL.md), then end your turn. What wakes you is a message whose first line is `#<n> REVIEW`, sent by the same call that posts the report; then read the ticket for the comment whose first line is `REVIEW ` |
| Start the verifier on your ticket | `<dispatch> start <n> verifier`, then that same `create_agent` path, then end your turn. The verifier finishing wakes you; then read the ticket for the comment whose first line is `VERDICT`. Start it once |
| You were woken for an agent you started and its result is not on the ticket | `<dispatch> wait <n> worker\|reviewer\|verifier`: prints the first line of its result comment (`ALL MET` / `HANDOFF REQUIRED`, `REVIEW …`, `VERDICT …`), reading the ticket before it waits at all |

The `wait` row and its exit codes are also what the main agent of a night reads: the command is the same one, whichever kind of agent it is asked about.

## Exit codes

**`start <n> reviewer|verifier`:**

| Code | What happened |
| --- | --- |
| `0` | One JSON object is on stdout. A second live-table row for that agent is nested as `fallback` |
| `2` | Nothing was started. The reason is on stderr — read it verbatim. Typical causes: the ticket is not `OPEN` / not `ready-for-agent` / still blocked; no live-table row for that agent; no recorded base commit (reviewer); the Paseo daemon could not be asked to register this checkout as a project; an argument this form does not take. A 2 here is a pipeline fault: `<engine> <n> --sub-issue pipeline <file>`, where the file's body is the command you ran and the output you saw, then stop |

**`wait <n> worker|reviewer|verifier`:** `0` the result comment is on the ticket and its first line is on stdout; `1` the agent is gone — `closed`, `error`, or no longer listed — and no result comment exists; stderr names the next step. An `idle` agent is not gone: an agent that has handed work to subagents and ended its turn sits at `idle` for the whole of that work, doing exactly what it was told, and `3` is the answer; `2` no agent labelled `mmw.ticket=<n>` of that kind; `3` still working, which covers `running`, `initializing` and `idle` — run it again. It reads the ticket before it waits at all, so a result already there returns at once. Otherwise it spends at least `MMW_WAIT_S` seconds (default 90) before answering `3`, re-reading the ticket every `MMW_WAIT_BEAT_S` seconds (default 10) — so `run it again` is a beat rather than a loop with nothing in it. It writes nothing.

No host kills a command that outlasts its shell tool: all of them move it to the background and hand back no exit code, which reads as neither `0` nor `3`. When that happens, run `wait` again — and if this host stops waiting sooner than 90 seconds, set `MMW_WAIT_S` below that bound.
