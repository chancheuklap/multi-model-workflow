---
name: verify-ticket
description: Run one ticket's acceptance criteria, and close the ticket when they pass. Use before you touch a ticket, once the code is written, when you are its verifier, when you are closing it out, when something has to be cut out of it, when you are handing back a report on it, and when a batch is about to be published.
---

# Verify ticket

Each acceptance criterion on a ticket carries a `CHECK:` command and the `EXPECT:` string a passing run prints. This skill runs them and comments the outcome on the ticket.

The ticket is the only state. Every run reads it fresh, writes at most one comment, and carries nothing to the next run.

## Resolve `<engine>` once

`<engine>` in every command below is `scripts/verify-ticket.py`, next to this file, and means:

```bash
python3 <absolute path to that script>
```

Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from.

A criterion names a judge by its bare name (`story-parity.py …`, `boundary-check.py …`, `journey.py …`, `harness-guard.py …`), and `<engine>` puts the directory that holds them on the `PATH` of the shell that runs it; nothing in a ticket says where this machine keeps its skills. That directory is the `scripts/` of the `drive-target` skill, which `<engine>` resolves from its own location, so no run has to name it. `--tools <directory>` overrides it and is repeatable. A run whose ticket names a judge that neither the directories in force nor `PATH` holds is refused before anything starts: exit 2, the script named on stderr, nothing run and no comment posted. A criterion failing `command not found` reads exactly like one that ran and did not pass.

## Find your run

| You are here | Read |
| --- | --- |
| About to touch ticket `<n>` | [references/claiming.md](references/claiming.md) |
| A **worker** with the code written, or the **verifier** on the ticket | [references/running-criteria.md](references/running-criteria.md) |
| Closing the ticket out | [references/closeout.md](references/closeout.md) |
| Cutting something out of the ticket | [references/sub-issues.md](references/sub-issues.md) |
| The **reviewer**, with the report written to a file | [references/reporting.md](references/reporting.md) |
| Publishing a batch, or opening a night on a spec | [references/linting.md](references/linting.md) |

No run of this skill tells anybody anything. What a run posts on the ticket is the news: the relay of the `dispatch` skill reads the event there and wakes the session waiting on it — the main agent for a `--closeout` either way, a `--preflight` that refuses and a `--sub-issue pipeline` or `decision`, the worker for a `--review` and a `--verdict`. A comment that lands is therefore a comment its reader hears about, whatever the run did after posting it.

## Reached from here

- **A criterion has to launch, reach or observe the running product; you are writing a story, boundary or journey criterion, or reading a `MISS` or `DIFF` line; the repository has no `.mmw/target.json`; you are about to touch a process or a port** → the `drive-target` skill. Its five rules while the product is running bind every run of this skill.
