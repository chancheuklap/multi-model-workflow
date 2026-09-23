---
name: verify-ticket
description: Run one ticket's acceptance criteria, and close the ticket when they pass. Use when something has to be cut out of a ticket, and when a batch is about to be published.
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

A criterion names a judge by its bare name (`story-parity.py …`); `<engine>` puts the `ui-acceptance` skill's `scripts/` on the `PATH` of the shell that runs a `CHECK:`, so a judge run by hand needs that directory on `PATH`.

## Find your moment

A worker's claim, criteria runs and closeout are steps of the `implement` skill.

| You are here | Read |
| --- | --- |
| Cutting something out of the ticket | [references/sub-issues.md](references/sub-issues.md) |
| About to publish a batch (its drafts), having published one, or opening a night on a spec | [references/linting.md](references/linting.md) |

## Reached from here

- **A criterion has to launch, reach or observe the running product; you are reading a `DIFF`, `MISS`, `JOURNEY` or `HARNESS` line; the repository has no `.mmw/target.json`; you are about to touch a process or a port** → the `ui-acceptance` skill. Its five rules while the product is running bind every run of this skill.
