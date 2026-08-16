# Plan coverage

**Who reads this:** the reviewer whose Goal starts with `Plan coverage`.

One ticket, one plan, one `worker`. Does the whole plan give an executable route.

Tickets in this round with no plan are normal when they still cannot be planned. Not a finding.

## Look

- Every ticket in this round has a plan. Every ticket criterion maps to `## Acceptance`.
- Walk spec `## Implementation Decisions` and `## User Stories`. Name the ticket that carries each item. No ticket is a finding.
- Step order holds. The `worker` does not guess product decisions. Local implementation inside settled bounds is allowed.
- Confirmed prototype decisions and named research files are in the route or in acceptance. Unknowns stay marked unknown.
- Each criterion has a test, an artifact, or a human result. UI tickets keep automated verify and human browser checks apart.
- Required migration, registry, docs, or rollback are present. Extra features outside the ticket are not.

## Always report

A criterion with no proof; steps that still miss the goal; a missing dependency; an open product decision left to the `worker`; a confirmed prototype decision left out; a secret, production act, or human gate with no gate.

**After a `worker` reads this plan, can they finish the ticket without reopening product decisions?** That is the only bar.
