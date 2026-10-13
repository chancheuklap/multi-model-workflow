# Tests for a feature present only in the design package

Use this branch when a design package has a feature the product does not yet
have. Write its feature file and e2e test from the signed-off design page.
The same test must pass with `--target design` and fail with `--target product`.
This is To tickets' Acceptance criteria rule for running a CHECK on a copy of
the spec's verbatim text: the design page is that copy.

For a new project without code, every feature takes this branch. Take Launch's
startup command from the spec's Implementation Decisions. The first ticket of
the first night is a smoke test proving the product starts and its home page
is reachable. Its criterion states that the base run is red because the product
cannot start. Hand over names that pending product proof. Do not call the
product half proven by a passing design run.

## Prepare per target, assert once

Keep one test for both targets. Split only preparation: `product` builds data
through the product's own entry; `design` opens the page drawn for that state.
Draw one state per page with the state in its name. Map route and state to page
files in `tests/e2e/<product>/helpers/design.ts`. Use one shared assertion block
for the visible result. Find elements only by roles, visible names, and labels;
take only fixed steps.

The spec's interface contracts and schema changes define the data shape.
The test creates its data through the UI or the API the page itself calls.
Copy expected values from the design page as literals in the test. Put repeated
login or activation steps in `tests/e2e/<product>/helpers/`, using the test
accounts named in Rules. Each run starts its own fresh local back end or data
directory, not pre-existing records. Design-package data is for drawing only;
the product target reads none of it.

Turn the feature file's stored half of `Proof` into an assertion: after the
operation, refresh the page or reopen the product and assert the data remains.
Go through the product's own entry, never query the database directly. On the
design target, refresh checks the drawn result; it is not proof of storage.

Intercept requests with `browser.route` only for external services, interfaces
not yet implemented, or errors and loading states that operations cannot
produce. For an unimplemented interface, put the response in the test using the
spec's interface contract. Once that interface lands, the owner names the
maintain-verification-skill skill; an interception no longer needed is a harness
gap. Do not replace a working local back end with design data.

Start from an entry the product already has, then find the new element. The
base run must fail at the missing feature, such as an element assertion,
not a navigation timeout. For a new project, the smoke ticket's inability to
start is the explicit exception described above.

Done when the feature file names its test, the design run passes, and the
product run fails for the missing feature, or the new project's smoke ticket
records the pending product launch proof.

## Notes example

The four files in `references/example/` are an example, not a product to copy.
Read `references/example/e2e.config.ts`,
`references/example/helpers/design.ts`,
`references/example/pin-note.e2e.ts`, and
`references/example/pin-note.md` together. Copy them to the locations their
comments name, adapting the product's own launch and entries.

This example Notes app already creates notes at `/notes`; pinning is the new
feature. Its `start` package command accepts `--port` and `--temporary-data`,
creates an empty temporary data directory, runs migrations, and removes its
own instance and scratch data on exit. A Notes app with an external back-end
stack calls its ensure script from that command. The design target serves the
repository root, so its base URL path `/design/notes/` identifies that target
to the test without a model or an invented e2e fixture. The page
`design/notes/notes-pinned.html` draws the `Release checklist` note with status
`Pinned` and the `Unpin Release checklist` button. The product preparation
creates and pins the same note; both targets use the same visible assertions
before and after refresh.
