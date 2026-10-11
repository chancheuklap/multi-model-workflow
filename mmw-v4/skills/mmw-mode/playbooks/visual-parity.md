### Visual parity

**You own pixel-exact equivalence. The baseline is the spec. You do not touch it.** Equivalence is verified by image diff, not by eye. A worker migrates, on one ticket.

1. **Open the ticket.** Open a ticket and its `fix-<n>` as `../references/ticket.md` `## Opening a ticket` says, with `Playbook: Visual parity` and the owner's words under `## Problem`. A ticket that already has its `fix-<n>`, such as one Grill with docs opened, keeps them. Done when the ticket is open and `fix-<n>` is on origin.
2. **Establish the baseline first**, before any migration: a visual regression harness that screenshots the current component across its states, plus the target when matching two implementations. No baseline, no parity claim. A blocking prerequisite, not a follow-up. Commit the harness and the baseline on `fix-<n>`. Done when the harness runs and its baseline is committed.
3. **Anti-shortcut clauses, stated and held:** no harness modifications, no baseline tampering, no component restructuring to make a diff pass. If the baseline looks wrong, stop and ask the owner, don't edit it. The baseline is a contract (**principle-baseline-is-the-contract**); a diff that will not reach zero is a defect to fix, never a check to bend (**principle-fix-root-causes**). Done when the clauses are written for step 4.
4. **Write the ticket.** Fill it in as `../references/ticket.md` `## Opening a ticket` says. **What to build** has the worker migrate one component at a time, shared primitives first as a blocking phase, running typechecking and single test files as it goes (**principle-run-the-smallest-test-set**), and carries the clauses of step 3. The harness and its baseline are baselines under **Read first**. One acceptance criterion per component: its image diff against the baseline is zero. Components too many for one ticket go through To spec and To tickets instead, one ticket per component. Done when every section below `## Problem` is filled.
5. **Hand it back.** As `../references/ticket.md` `## Handing it back` says. Done when the owner has said go and One ticket runs, or the ticket is in `needs-triage` or closed.

**The image diff.** One ticket step 4 runs this once the ticket passed: verify each component against its baseline via image diff on the matching surface via the control skill, in `.worktrees/issue-<n>`. A nonzero diff is a fail. Investigate the pixel delta.

**A ticket that came back.** When the owner picks it from `needs-triage`, read why on the ticket and go back to step 3 with that evidence.

**Reply:** the components in scope, the baseline harness location and what it captures, the criteria, what the ticket leaves out.
