### Visual parity

**You own pixel-exact equivalence. The baseline is the spec. You do not touch it.** Equivalence is verified by image diff, not by eye.

1. Establish the baseline first, before any migration: a visual regression harness that screenshots the current component across its states, plus the target when matching two implementations. No baseline, no parity claim. A blocking prerequisite, not a follow-up.
2. Anti-shortcut clauses, stated and held: no harness modifications, no baseline tampering, no component restructuring to make a diff pass. If the baseline looks wrong, stop and ask, don't edit it.
3. Migrate one component at a time. Parallelize across worktrees, one owner per component (the [principle-separate-before-serializing-shared-state](../../principle-separate-before-serializing-shared-state/SKILL.md) principle skill). Shared primitives migrate first as a blocking phase.
4. Compare each component with its baseline by image diff using the project's `verify-<app>` for that surface, or [verify-this](../../verify-this/SKILL.md) if none matches. A nonzero diff is a fail. Investigate the pixel delta. Schedule recurring checks for each component until its diff is zero.
5. Run **Opening a PR** for the code ticket covering the agreed component or safe batch.

**Reply:** components migrated, the diff result for each, the baseline harness location, what's left.
