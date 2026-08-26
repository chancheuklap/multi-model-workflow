# Spec alignment

**Who reads this:** the reviewer whose Goal starts with `Spec alignment`.

Does this spec fit this repo's own contracts — domain terms and engineering rules, not generic best practice.

## Look

- Words and data landings match the domain docs (`mmw domain path` prints the shape and the path to read) and the ADRs `mmw artifact index adr` lists. One structure is not copied as a second source of truth.
- Declared invariants hold — money, permissions, identity.
- New things other code will call are designed as registered: ports, commands, billable actions, capabilities, migrations, ADRs.
- The spec records real decisions, not a filled template.
- Prototype and research the task named are cited as indexes plus the files they list. Stale snapshots are not current fact.

## Always report

A broken invariant; a dependency on infrastructure that does not exist; a cross-boundary contract missing provider or consumer; a bypass of this repo's contract, registry, or migration; production risk with no design.

If those docs are not in Read, `needs-context`. Do not guess this repo's rules.
