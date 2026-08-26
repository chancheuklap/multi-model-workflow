# Plan compliance

**Who reads this:** the reviewer whose Goal starts with `Plan compliance`.

Does this plan obey the repo's contracts, and can several plans join on one task branch.

## Look

- Paths, symbols, tables, and interfaces the plan says exist are in current source. New files are marked `Create`.
- Edits fit this repo's module bounds, registry, migration, naming, and release rules.
- One owner per shared file in the Change Maps. Provider and consumer cite the same `## Contract Boundaries` entry name. Field copies in the plan are a finding. Dependency order holds.
- Tests use seams the spec already confirmed and commands the repo already has. A new seam invented at plan time is a finding.
- Named prototype and research files exist. Rejected variants are not the current route. Unknowns are not written as current fact.
- Data, infra, billing, permissions, and shared state include migration, rollback, or a human gate when they need one.

Do not report a missing full implementation, a copied TDD lecture, a test pyramid, a complexity score, or a commit-by-commit schedule.

## Always report

A cite that does not exist; a broken hard rule; a cross-plan interface missing provider or consumer; two plans claiming the same file; a seam that is not the spec's; high-risk work with no migration, rollback, or gate.
