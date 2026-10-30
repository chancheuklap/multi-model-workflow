---
name: prepare-ui-acceptance
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Prepare UI acceptance

Prepare this ticket's UI acceptance from its agreed baseline, using the product's existing verify-<product> skill. Return the test, feature registration, command and evidence to the calling preparation. This method neither generates runtime tools nor runs whole-product maintenance. The **to-tickets** skill's **Prepare verification** in `references/ticket-format.md` supplies missing reusable capability first.

Use the **test-audit** skill's writing branch. Keep the caller's product, issue, effort checkout, settled behavior and existing proof. Read the product skill's Read first, Rules, Launch, Drive and Evidence, then the affected feature files. Use Cleanup after resources you start. Reuse a matching prepared result rather than writing or running it again.

## Choose the baseline

| Work | Method |
| --- | --- |
| New or changed UI design | **New design** below: the approved winner and final interface contract |
| Repair with a settled expected behavior | **Repair** below: the requirement and original reproduction, no invented prototype |
| Structure changes while behavior stays unchanged | **Preserve behavior** below: current product behavior and existing tests |
| Correct an erroneous frozen test | **Correct acceptance** below: the orchestrator's recorded contract resolution |

## New design

Write tests per ticket after the interface contract is final and the prototype's API fake matches it. Start from the feature file's Proof. The Design a UI playbook owns missing UI choices; return one to the caller instead of inventing it. Tests and feature files remain read-only to implementation workers, and their CHECK runs only product.

## One path for both targets

The prototype mounts at the feature file's final `Route:`;
for an interface without its own route, it mounts in the module that renders it.
`design` must pass and `product` must fail at the missing feature, not a navigation
timeout. Start from an entry the product already has, then find the new element.
After the mount points are removed, the tests stay unchanged.

Capture `app.screenshot('<state>')` at the states to compare with the prototype.
The Spec reviewer uses these frames to compare the same state on both targets.
Assertions prove what the user sees and can accomplish. The ticket's back-end
tests prove storage. A slice
with back-end work also gets a back-end test CHECK naming its dedicated test
database, separate from e2e data.

For an affected existing feature in this new-design branch, keep its registered tests as pins when
behavior stays unchanged. When behavior changes, rewrite its old tests from
the prototype. Give each ticket's acceptance tests a new file under
`tests/e2e/<product>/`, register it in the feature file's `Tests:` line, and use
one CHECK for that file. Sharing a pin file makes unrelated work fail together;
two CHECKs for one file overwrite its evidence.

Before dispatch, run the ticket's test on `design` again. A failure means the
API fake has not caught up with the final contract.

Done when `Proof` precedes the test, the feature file names it, `design` passes,
and `product` fails for the missing feature. Existing pins pass on the base.

## New projects without code

Launch the standalone prototype with the effort's chosen stack. Take the product startup command from the prepared spec's Implementation Decisions or the independent change's What to build. The first implementation ticket is a smoke ticket that builds the product skeleton and proves
its launch and reachable home page. Its base criterion is red because the
product cannot start. This is the exception to failing at a missing feature.
Prove the feature on `design` and record the pending product launch proof in
Hand over. A passing prototype run does not prove the product half.


## Repair

Use the settled requirement and runtime reproduction. Read the feature's Gotchas. Reuse the original failing product loop or write its focused fixed-step e2e test. Demonstrate the described failure on the actual product baseline; a missing file or broken fixture is not that defect. Register this ticket's new test file on the affected feature, creating its description from the actual product and agreed requirement when absent. No design target or winner is required when there is no new design question. Return the failure evidence and command to bug-fix or the ticket writer; the worker fixes the product, not this test.

## Preserve behavior

Reuse the affected feature's registered tests as pins. Where none exists, write a focused test from current behavior and register it. Prove it green on the baseline and demonstrate sensitivity with test-audit's pin-writing method. Return its command and evidence before the structural move. No new prototype is required. The worker keeps this prepared acceptance unchanged and proves the same behavior after the move.

## Correct acceptance

Only the owner or original orchestrator corrects frozen acceptance after publication. Read the contract resolution, then enter New design, Repair or Preserve behavior for its actual baseline. A changed UI design first returns to Design a UI and owner confirmation. Commit and push the corrected assets on the same effort branch and return the exact change and proof to the existing contract handler; this method does not resume workers or change the ticket's authority itself.

## Register and return

Keep the feature-file format in the **create-verification-skill** skill's **3. Seed the feature map**. Update the changed behavior from its settled sources, put Proof before its test, and commit Tests and Driving it with e2e with that test. Each ticket owns a new e2e file; keep unchanged pins in their registered files. Copy the product's complete Launch command, with config, preparation and independent output path, for the writer's CHECK. Preserve backend proof separately from e2e.

Commit and push the prepared test, feature registration and description on the caller's effort branch before execution. Return their paths, the baseline used, the complete command, the observed result and evidence paths, and any unproved scope. Missing access or an unsupported target returns the specific prerequisite to the caller, not a claimed pass. Existing UI assets stay read-only during execution.

## Notes example

For a New design two-target handoff example, read [notes-example.md](references/notes-example.md).
