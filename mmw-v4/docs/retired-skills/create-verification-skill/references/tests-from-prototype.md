# Write tests from the prototype

Use the **test-audit** skill's writing branch for acceptance-test methods. This file owns the prototype-to-product handoff and evidence registration.

Write tests in the day, per ticket, after the interface contract is final and
the prototype's API fake matches it. Start with the feature file's `Proof`,
then write the test. At night, tests and feature files are read-only and CHECK
runs only `product`.

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

For an affected existing feature, keep its registered tests as pins when
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

Launch the standalone prototype with the effort's chosen stack. Take the product
startup command from the spec's Implementation Decisions. The first ticket of
the first night is a smoke ticket that builds the product skeleton and proves
its launch and reachable home page. Its base criterion is red because the
product cannot start. This is the exception to failing at a missing feature.
Prove the feature on `design` and record the pending product launch proof in
Hand over. A passing prototype run does not prove the product half.

## Notes example

Read `references/example/e2e.config.ts`, `references/example/pin-note.e2e.ts`,
`references/example/pin-note.md`, and `references/example/verify-notes.SKILL.md`
together. They illustrate a Notes app that already creates notes at `/notes`;
pinning is the new feature.

The product's environment tool runs as `bash scripts/dev/notes.sh`. Its `serve` command
accepts `--port` and `--temporary-data`, creates a fresh data directory, runs
migrations, and removes its instance and scratch data on exit. It serves a
production build. `NOTES_PROTOTYPE=1` selects the prototype at `/notes` through
the same command, including the real backend for existing note creation. The
prototype's new pin interface uses an API fake seeded from the environment tool.
This example has no external back-end stack and no accounts.

Both targets create `Release checklist`, pin it, check the visible result, and
capture `pinned-note`. The config disables retries because data is fresh per
run, not per attempt. Rerun the CHECK for fresh data after a failure. These are
illustrative files, not a runnable Notes product shipped with this skill.
