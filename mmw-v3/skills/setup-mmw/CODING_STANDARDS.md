# Coding standards

The rules the review applies to every change in this repository. The Standards axis applies `## Code` and the Tests axis applies `## Tests`.

The author of a change does not read this file. Writing the change already takes more context than anything else in the work, and the review has room to spare, so the rules are applied where they are read: here, against the diff. A rule here is a judgement the diff shows. A violation with a fixed shape (a banned call, an import form, a file location) is a check that fails, not a row. A row is added, changed or removed only through a retro proposal the owner approved.

Name each finding by its rule and quote the lines it is about. Every rule is a judgement call. **Details** names where the reasoning and the examples are.

## Code

| Rule | A finding when the diff | Details |
| --- | --- | --- |
| Old path kept | adds a path that does the job of an existing branch, guard, helper or file, and leaves the old one, or a caller still on it, in place | **principle-migrate-callers-then-delete-legacy-apis** |
| Fix at one caller | fixes a defect at the one caller that met it, while the shared code it comes from still hands it to the other callers | **principle-migrate-callers-then-delete-legacy-apis** |
| Unexplained addition | adds a file, a dependency or a configuration entry, and neither the change nor its author's recorded decisions say why the existing one was not enough | **principle-laziness-protocol** |
| Lost safeguard | simplifies away a security check, error handling that prevents data loss, accessibility, or anything the request explicitly asked for | **principle-laziness-protocol** |
| Silent pass | lets a check, a guard or a script that verified nothing (no file matched, no case ran, a source could not be read) report success | **principle-a-check-must-be-able-to-fail** |
| Narrating comment | adds a comment that restates the code or narrates steps (`// Phase 1: add cards`), where only a non-obvious why earns a comment | the `mmw-mode` skill's `## Comments` |
| History in a file | writes into a file, a comment or a docstring what changed ("now", "previously", "no longer"), not what is true of its subject | **principle-files-describe-the-present** |

## Tests

| Rule | A finding when a case in scope | Details |
| --- | --- | --- |
| Cannot fail | would still pass if every function it imports returned `undefined`; for a behaviour the change keeps, does not observe that behaviour. Ask this first: it is the finding whatever else the case is | **principle-a-check-must-be-able-to-fail** |
| Tautological | expects a value restated from the implementation, so it passes by construction | the `tdd` skill's `tests.md`, **Tautological tests** |
| Implementation-coupled | mocks internal collaborators, tests private methods, or asserts call counts or order, so a refactor that keeps the behaviour breaks it | `tests.md`, **Implementation-detail tests** |
| Side channel | verifies through external means (a database read, a file the code writes) where the interface shows the result | `tests.md`, the red flag "Verifying through external means instead of interface" |
| Named for the how | has a name that says how the code works, not what it does | `tests.md`, the red flag "Test name describes HOW not WHAT" |
| Over-mocked | mocks something the repository can run, not a system boundary | the `tdd` skill's `mocking.md`, its "Don't mock" list |
| Only the happy path | covers the ordinary input only, while the code has an edge, a boundary or an error path the requested behaviour depends on; the finding names that path and what should happen on it | |
| Pins wording | asserts the wording of prose no program reads (a skill's text, a document, a message nothing parses), where the request fixes no such text word for word; it fails each time the text improves and proves nothing about behaviour | |
| Unasked test | is committed although no criterion names it and the repository keeps no test of this kind for this kind of change, or adds more than one focused case for one stated behaviour | |
