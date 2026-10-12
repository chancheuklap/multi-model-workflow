### Feature

**You own the design and the ticket that carries it. A worker writes the code, and you verify it on the product.**

1. **Open the ticket.** Open a ticket and its `fix-<n>` as `../references/ticket.md` `## Opening a ticket` says, with `Playbook: Feature` and the owner's words under `## Problem`. A ticket already open, such as one Grill with docs opened, keeps its number and opens only the `fix-<n>` it lacks. Done when the ticket is open and `fix-<n>` is on origin.
2. `how` over the affected subsystem. Read the files the change touches before concluding anything about them (**principle-read-before-you-conclude**), and look for what already does the job before designing one (**principle-start-from-what-exists**).
3. Settle the throughput checkpoint, one answer per dimension. A dimension that genuinely does not apply (single file, no fan-out) is answered `n/a: <reason>` rather than dropped:
   - **Blocking first steps.** Gates run before fan-out.
   - **Independent workstreams.** Disjoint files, services, or layers parallelize. Shared writes serialize.
   - **Shared mutable state.** Default to splitting the target (the **separate-before-serializing-shared-state** principle skill). Serialize only for real invariants.
   - **Smallest safe decomposition.** If one ticket can carry it, name why.

   The checkpoint decides the size. One ticket can carry the change: go on to step 4. It cannot, or its independent workstreams should run in parallel: go to step 6 now and say so, and the owner's word sends it to To spec, as `../references/ticket.md` `## Handing it back` says for a change too big for one ticket. Done when the checkpoint names one ticket or To spec.
4. `architect` for the design, which decides how many candidates it needs. Its sketch goes in `efforts/<effort>/prototypes/<n>/SKETCH/`, named as the **prototype** skill's rule 1 names them, committed on `fix-<n>`.
5. **Write the ticket.** Fill it in as `../references/ticket.md` `## Opening a ticket` says. **What to build** sets the scope the worker writes to: the named data shape and its organizing structure per **principle-model-the-domain** (a state machine over scattered booleans, a table or registry over branching, a typed model over repeated shape assumptions), chosen before any logic is written; surgical edits, re-grounded against the source for upstream-derived files; a shared-primitive improvement ported to every consumer and verified in each. When `architect` produced a sketch, it is a baseline under **Read first**, and **What to build** says the sketch is the contract: its `not implemented` bodies become code and its pseudocode becomes logic, a deviation from it is surfaced as a `contract` child rather than absorbed, and it can land as its own commit first (the **foundational-thinking** principle skill), with planned and scoped breakage while its bodies are filled in (the **outcome-oriented-execution** principle skill). Every other baseline the code must follow is under **Read first** too, copied, not restated from memory (**principle-baseline-is-the-contract**). The acceptance criteria are tests of the behavior the sketch and the owner's words describe, at the ticket's **Seam**. Done when every section below `## Problem` is filled.
6. **Hand it back.** As `../references/ticket.md` `## Handing it back` says. Done when the owner has said go and One ticket runs, or the ticket is in `needs-triage` or closed.

Parent-level fan-out is for slices that produce independent artifacts (audits, cross-subsystem investigations, competing experiments), not for writing the change.

**Verify on the matching surface.** One ticket step 4 runs this once the ticket passed: drive the new behavior in `.worktrees/issue-<n>` the way its user meets it, through the matching control skill. "Inconclusive" or wrong-surface is not a pass. Flag it. Run the smallest test set that proves the change (**principle-run-the-smallest-test-set**).

**A ticket that came back.** When a ticket its worker handed back (a `ticket.returned` event) is picked from `needs-triage`, read why on the ticket and go back to step 3 with that evidence.

**Reply:** what the change does for its users, the design chosen and why (tables for design alternatives), the throughput checkpoint, the criteria, what the ticket leaves out, open decisions.
