# Bar for entry

Every rule above says what a good test *is*. This file is the gate: a test that fails any line here does not go in, and a review sends it back.

## Rules

- **One behaviour, one test, at the layer that owns it.** Don't assert the same fact again a layer up or down to lift a coverage number.
- **Build test data through the real producer path** — the shared builder the production code uses. Never hand-roll a second copy of the producer's shape; the copy drifts and the test keeps passing.
- **A bug's regression test lives in the file that owns that behaviour.** Never a new `fix_xxx` file — the behaviour has a home already, and a parallel file means nobody reading that home sees the case.
- **Values the system owns elsewhere are read from their source, not retyped.** Prices, user-facing copy, enum members: read the authoritative source and compare. This sharpens the independent-source-of-truth rule rather than contradicting it — for a *computed* result the independent source is a known-good literal; for a value the system already holds, it is that source.
- **When a behaviour is retired, its test dies in the same commit.** A `skip` that outlives one iteration is deleted, not left as a marker.
- **Production code carries no test-only seam.** No `_for_test` back doors, no branches that exist because a test needed them. Testability comes from dependency injection and from returning results instead of reaching into state.
- **The repo's own test guards, lint, and type checks must pass.** That is the machine floor. Green proves nothing about whether the test is worth keeping.

## Forbidden forms

Each of these is a defect on sight, however green it runs.

| Forbidden | Why | Instead |
| --- | --- | --- |
| Asserting on source text (grepping code or docs for a literal or a private symbol) | Renaming turns it red for nothing; routing round the literal makes it miss the real break. It locks the implementation, not the behaviour | Call the real function or command and assert the observable result; if you must assert structure, parse it (AST) rather than match text |
| Locking UI copy or prose word for word | An edit for tone turns it red; prose is not a contract | Assert the semantic key or state; read the copy from its single source and compare |
| Mirroring a whole field set, default set, or enum into the assertion | It copies the contract schema into a second place, so one change needs two edits | Go through the real contract type on a real producer→consumer path |
| Counting things in documentation (this file contains N words, that list has M items) | Editing the doc turns it red | Don't assert on docs; read the fact from the code that owns it |
| Tombstone path lists (retired files asserted absent one by one, archived files asserted present) | The list rots silently, and any tidy-up turns it red | Assert only which top-level directories should and shouldn't exist; an import that creeps back will fail a behaviour test on its own |
| Meta-gates that test the tests (asserting some suite list contains a given test file) | Suite membership is derived from the directory; a registry of it has no reason to exist | Delete it |
| Per-file allowlists (a hardcoded list of production paths, exempt or required) | It couples to the layout, and entries fail silently as the layout moves | Walk the structure and express the exception as a condition, not a list |
| Mocking your own services or stubbing your own seams | The stub and the real implementation drift, and a green test hides a real break | Run your own seams for real; mock only at an outside supplier's boundary |

## The admission question

Before a new test goes in, answer it: **which user journey, which money, or which data does this test guard — and who gets hurt the day it breaks?**

No answer means the test hasn't earned its place.
