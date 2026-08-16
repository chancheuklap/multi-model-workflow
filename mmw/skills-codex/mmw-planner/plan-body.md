# Plan body

One ticket, one plan. A `worker` reads the whole file in order.

Required: **Goal**, **Change Map**, ordered **Implementation** steps with a verify command, **Acceptance** covering every ticket criterion. Write the other sections only when they apply. Omit them when they do not — do not fill them with "N/A".

```markdown
---
ticket: <GitHub issue number>
artifact_refs: []
---

# Plan: <ticket title>

**Goal:** <observable result when this ticket is done>
**Source spec:** <spec path>
**Source ticket:** <tracker id>

## Change Map

| Path | Action | Role |
| --- | --- | --- |
| `path` | Create / Modify / Test / Docs | What this file does for this ticket |

## Implementation

1. **<observable checkpoint>**
   - Change: <behaviour that changes>
   - Files: <paths and roles>
   - Verify: `<command>` → <expected result>

## Acceptance

| Ticket criterion | Proof | Command or human result |
| --- | --- | --- |
| <criterion> | <test, artifact, or observable behaviour> | `<command>` → <expected result> |
```

Optional, when they apply:

- **Constraints** — project rules and spec decisions that bind this ticket, each with a source.
- **Current State** — current behaviour this route depends on, with paths and symbol names. No line numbers; the `worker` confirms them at start.
- **Contracts and Seams** — the spec seam this ticket uses; consumes / produces by the **name** of the entry in spec `## Contract Boundaries` (owner, provider, consumer). Cite the name; do not copy fields.
- **Prototype / research source** — chosen artifact and the files this ticket uses, when the ticket names them.
- **Browser** — for UI tickets, the pages and visible results a human checks. Automated verify stays in Implementation / Acceptance; the two do not stand in for each other.
- **Rollback and gates** — data, infrastructure, billing, permissions, shared state, or a human gate.

Steps follow real dependencies. One step is one observable checkpoint. No fixed minute count.

The plan locks settled behaviour, contracts, and risk bounds. The `worker` chooses local implementation inside those bounds. Default: no implementation code. Write a complete snippet only when a public contract, data shape, or algorithm cannot be said in prose.

Acceptance maps each ticket criterion onto a spec seam or a human browser check, using commands the repo already has. Testing method stays in `$mmw:mmw-tdd` and the repo `TESTING.md`.
