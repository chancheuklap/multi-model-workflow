---
name: verify-ticket
description: Run one ticket's acceptance criteria, and close the ticket when they pass. Use before you touch a ticket, once the code is written, when you are closing it out, when something has to be cut out of it, when you are posting a review report on it, and when a batch is about to be published.
---

# Verify ticket

Each acceptance criterion on a ticket carries a `CHECK:` command and the `EXPECT:` string a passing run prints. This skill runs them and posts the outcome on the ticket as an event.

The ticket is the only state. Every run reads it fresh, writes its events, and carries nothing to the next run. Every comment it posts is an event: a first line for a person and a trailing `<!-- mmw {...} -->` block, which is the only part any program reads.

## Resolve `<engine>` once

`<engine>` in every command below is `scripts/verify-ticket.py`, next to this file, and means:

```bash
python3 <absolute path to that script>
```

Resolve it from this file's own location; the path differs by machine and by host.

A criterion names a judge by its bare name (`story-parity.py …`, `boundary-check.py …`, `journey.py …`, `harness-guard.py …`), and `<engine>` puts the `scripts/` of the `ui-acceptance` skill, resolved from its own location, on the `PATH` of the shell that runs it. `--tools <directory>` overrides it and is repeatable. A run whose ticket names a judge that neither the directories in force nor `PATH` holds is refused before anything starts: exit 2, the script named on stderr, nothing run and no comment posted.

## Find your run

| You are here | Read |
| --- | --- |
| About to touch ticket `<n>` | [references/claiming.md](references/claiming.md) |
| A **worker** with the code written, or the main agent re-running landed work | [references/running-criteria.md](references/running-criteria.md) |
| Closing the ticket out | [references/closeout.md](references/closeout.md) |
| Cutting something out of the ticket | [references/sub-issues.md](references/sub-issues.md) |
| The **reviewer**, with the report written to a file | [references/review-report.md](references/review-report.md) |
| About to publish a batch (its drafts), having published one, or opening a night on a spec | [references/linting.md](references/linting.md) |

What a run posts on the ticket is how the waiting session learns of it: the relay of the `dispatch` skill reads the event there and wakes the session waiting on it — the main agent for a `--closeout` either way, a `--preflight` that refuses and a `--sub-issue` of kind `contract`, `fault` or `decision`, and the worker for a `--review`. A comment that lands therefore wakes its reader, whatever the run did after posting it.

## Reached from here

- **A criterion has to launch, reach or observe the running product; you are writing a story, boundary or journey criterion, or reading a `MISS` or `DIFF` line; the repository has no `.mmw/target.json`; you are about to touch a process or a port** → the `ui-acceptance` skill. Its five rules while the product is running bind every run of this skill.
