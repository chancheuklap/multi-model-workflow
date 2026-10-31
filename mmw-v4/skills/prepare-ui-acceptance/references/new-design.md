# Prepare acceptance for a new design

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

For a two-target handoff example, read [notes-example.md](notes-example.md).
