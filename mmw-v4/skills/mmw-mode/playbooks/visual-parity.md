### Visual parity

**You own pixel-exact equivalence. The baseline is the spec. You do not touch it.** Equivalence is verified by image diff, not by eye.

1. Establish the baseline first, before any migration: a visual regression harness that screenshots the current component across its states, plus the target when matching two implementations. No baseline, no parity claim. A blocking prerequisite, not a follow-up.
2. Anti-shortcut clauses, stated and held: no harness modifications, no baseline tampering, no component restructuring to make a diff pass. If the baseline looks wrong, stop and ask, don't edit it. The baseline is a contract (**principle-baseline-is-the-contract**); a diff that will not reach zero is a defect to fix, never a check to bend (**principle-fix-root-causes**).
3. Migrate one component at a time. Components that share no file can migrate in parallel, each on a native subagent of the host in its own git worktree, with step 2's clauses and its baseline in the prompt (the **separate-before-serializing-shared-state** principle skill); a subagent sends out no other, and you read its diff and its image diff before merging it back. Shared primitives migrate first as a blocking phase.
4. Verify each component against its baseline via image diff on the matching surface via the control skill. A nonzero diff is a fail. Investigate the pixel delta. Repeat per component until the diff is zero.
5. Run **Shared closing** once for the whole change (`playbooks/shared-closing.md`).

**Reply:** components migrated, the diff result for each, the baseline harness location, what's left.
