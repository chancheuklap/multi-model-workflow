### Refactoring

**You own the contract. The structure changes. The behavior does not.** Distinct from Feature, which adds behavior, and Bug fix, which corrects it. A worker moves the code, on one ticket.

If the cleanup reveals a missing feature or a real bug, split it out and ship the structural change first against the pinned contract. A redesign is allowed, but name it and route to Feature. Large or cross-cutting structural work belongs to the **figure-it-out** skill. This playbook is the focused-to-medium change.

1. **Open the ticket.** Open a ticket and its `fix-<n>` as `../references/ticket.md` `## Opening a ticket` says, with `Playbook: Refactoring` and the owner's words under `## Problem`. A ticket that already has its `fix-<n>`, such as one Grill with docs or Bug fix opened, keeps them. Done when the ticket is open and `fix-<n>` is on origin.
2. **Learn the contract and choose the pin.** Run the **how** skill over the affected subsystem to learn the contract, then choose the characterization test, snapshot, or equivalence harness that will capture current behavior before any structure moves. Where the area has no coverage, the pin is new. Type check and lint are not a pin. Read every file the move touches before deciding the contract (**principle-read-before-you-conclude**). Done when the contract and its pin are named.
3. **Name the structure the code is missing** per **principle-model-the-domain**. Boring code stays when the shape is already clear and local. The reshape must delete branches or invalid states, not add indirection. Done when the missing structure is named, or you have found the shape already clear.
4. **Name the target shape.** State what the module layout, types, and call graph should be if built today (**principle-foundational-thinking**, **principle-redesign-from-first-principles**). If the target crosses a function boundary, run the **architect** skill for parallel design exploration of the shape before the move, and commit its sketch on `fix-<n>`. Reuse a helper or pattern the repository already has before writing one (**principle-start-from-what-exists**). Done when the target shape is stated.
5. **Write the ticket.** Fill it in as `../references/ticket.md` `## Opening a ticket` says. **What to build** carries the move, which the worker does:
   - Write the pin first and run it green before any structure moves.
   - Subtract before you add: delete dead code, collapse one-caller wrappers, drop redundant validators, and remove orphan references before introducing the new shape (**principle-subtract-before-you-add**). The smallest change that reaches the target shape ships (**principle-laziness-protocol**).
   - Move in small behavior-preserving steps, each keeping the pin green, with typechecking and single test files run as it goes (**principle-run-the-smallest-test-set**). For API reshapes, migrate every caller and delete the old API in the same wave (**principle-migrate-callers-then-delete-legacy-apis**). No compatibility shims, no parallel old-and-new paths. Spot-check every rename against the actual files: renames silently miss usages in strings, prose, and back-references.
   - Commit in order: a subtraction commit, then the reshape, then any follow-on cleanup, each slice green before the next (the **sequence-verifiable-units** principle skill).

   The target shape, and the `architect` sketch when there is one, are baselines under **Read first**. The first acceptance criterion is the pin, green before and after; for a larger reshape, the second is an equivalence check: a script that diffs old-vs-new outputs, or a recorded baseline replayed against the new code. Done when every section below `## Problem` is filled.
6. **Hand it back.** As `../references/ticket.md` `## Handing it back` says. Done when the owner has said go and One ticket runs, or the ticket is in `needs-triage` or closed.

**Prove behavior is unchanged.** One ticket step 4 runs this once the ticket passed, with the next one: on the real artifact in `.worktrees/issue-<n>`, not "it compiles" (**principle-prove-it-works**). Run the equivalence check, or a smoke run on the matching surface via the relevant control skill, and the smallest test set that proves it (**principle-run-the-smallest-test-set**).

**Confirm the change is worth keeping.** The success measure is reduced reader load (**principle-minimize-reader-load**). If the diff does not lower reader load somewhere, it does not land.

**A ticket that came back.** When the owner picks it from `needs-triage`, read why on the ticket and go back to step 4 with that evidence.

**Reply:** the contract and the pin it is held against, the missing structure and the target shape, the equivalence check, the criteria, what the ticket leaves out. No new behavior.
