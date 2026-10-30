### Refactoring

**You own the contract. The structure changes. The behavior does not.** Distinct from Feature, which adds behavior, and Bug fix, which corrects it. A worker moves the code, on one ticket.

If the cleanup reveals a missing feature or a real bug, split it out and ship the structural change first against the pinned contract. A redesign is allowed, but name it and route to Feature. Structural work that one ticket cannot carry goes back to the owner through To spec (`playbooks/to-spec.md`). This playbook is the focused-to-medium change.

1. **Open the ticket.** Open a ticket and its `fix-<n>` as `../references/ticket.md` `## Opening a ticket` says, with `Playbook: Refactoring` and the owner's words under `## Problem`. A ticket already open, such as one Grill with docs or Bug fix opened, keeps its number and opens only the `fix-<n>` it lacks. Done when the ticket is open and `fix-<n>` is on origin.
2. **Learn the contract and choose the pin.** Run the **how** skill over the affected subsystem to learn the contract, then choose the characterization test, snapshot, or equivalence harness that will capture current behavior before any structure moves. Where the area has no coverage, the pin is new. Find the affected existing features as `../references/feature-map.md` says. For UI behaviour, read the `verify-<product>` skill's Read first and Rules. Take the e2e tests already registered in the feature map as pins; where none exists, read Drive and Evidence, write a test from the current code and register it on the feature file's `Tests:` line. Use Cleanup after running a product you started. For non-UI behaviour, write the chosen pin as a characterization test that captures current behavior. This session prepares every pin, commits it and any feature file registration on `fix-<n>`, and pushes before the worker starts. Each pin meets the **test-audit** skill's pin-writing method. Read every file the move touches per **principle-read-before-you-conclude** before deciding the contract. Done when the contract is named and every pin is on origin's `fix-<n>`.
3. **Name the structure the code is missing** per **principle-model-the-domain**. Done when the missing structure is named, or you have found the shape already clear.
4. **Name the target shape.** State what the module layout, types, and call graph should be if built today (**principle-model-the-domain**, **principle-redesign-from-first-principles**). Run the **prototype** skill on the target shape before the move; its `## Pick a branch` decides whether a sketch is drawn, committed on `fix-<n>`. Follow **principle-start-from-what-exists** before writing a helper. Done when the target shape is stated.
5. **Write the ticket.** Fill it in as `../references/ticket.md` `## Opening a ticket` says. **What to build** carries the move, which the worker does:
   - The pin is already on `fix-<n>`; run it green before any structure moves.
   - Follow **principle-subtract-before-you-add** for removal order and the size of the new shape.
   - Move in small behavior-preserving steps, each keeping the pin green, and commit them as **principle-sequence-verifiable-units** says; test per **test-audit**. For API reshapes, follow **principle-outcome-oriented-execution**. Spot-check every rename against the actual files: renames silently miss usages in strings, prose, and back-references.

   The target shape, and the sketch when there is one, are baselines under **Read first**. The first acceptance criterion is the pin, green before and after; for a larger reshape, the second is an equivalence check: a script that diffs old-vs-new outputs, or a recorded baseline replayed against the new code. Done when every section below `## Problem` is filled.
6. **Hand it back.** As `../references/ticket.md` `## Handing it back` says. Done when the owner has said go and One ticket runs, or the ticket is in `needs-triage` or closed.

**Prove behavior is unchanged.** One ticket step 4 runs this once the ticket passed, with the next one: on the real artifact in `.worktrees/issue-<n>` (**principle-prove-it-works**). Run the equivalence check, or a smoke run on the matching surface via the relevant control skill, and tests per **test-audit**.

**Confirm the change is worth keeping.** The success measure is reduced reader load (**principle-minimize-reader-load**). If the diff does not lower reader load somewhere, it does not land.

**A ticket that came back.** When a ticket its worker handed back (a `ticket.returned` event) is picked from `needs-triage`, read why on the ticket and go back to step 4 with that evidence.

**Reply:** the contract and the pin it is held against, the missing structure and the target shape, the equivalence check, the criteria, what the ticket leaves out. No new behavior.
