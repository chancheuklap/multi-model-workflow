---
name: verify-ticket
description: Run one ticket's acceptance criteria, and close the ticket when they pass. Use when something has to be cut out of a ticket, and when a batch is about to be published.
---

# Verify ticket

Each acceptance criterion on a ticket carries a `CHECK:` command and the `EXPECT:` string a passing run prints. This skill runs them and posts the outcome on the ticket as an event.

The ticket is the only state. Every run reads it fresh, writes its events, and carries nothing to the next run. Every comment it posts is an event: a first line for a person and a trailing `<!-- mmw {...} -->` block, which is the only part any program reads.

How a criterion is written is the **to-tickets** skill's `references/ticket-format.md`.

## Find your moment

A worker's claim, criteria runs and closeout are steps of the mmw-mode skill's Work a ticket playbook.

| You are here | Read |
| --- | --- |
| Cutting something out of the ticket | [references/sub-issues.md](references/sub-issues.md) |
| About to publish a batch (its drafts), having published one, or opening a night on a spec | [references/linting.md](references/linting.md) |
