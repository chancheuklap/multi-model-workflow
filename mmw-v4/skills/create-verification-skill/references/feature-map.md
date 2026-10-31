# Record the feature map

Create one file per user-facing feature under
`.agents/skills/verify-<product>/features/`, the top three to five first, from
routes, navigation, or docs. Follow
`references/example/pin-note.md` for the feature file. Each file starts with these three lines:

```text
# <feature name>
Route: <route or entry>
Tests: <file>, <file>, …
```

`Tests:` lists the covering files under `tests/e2e/<product>/`, separated by
commas. Each ticket changing this feature adds its own file. A feature without
a test has `Tests: none`. There is no hand-written index or status field:
the header shows test coverage, and unfinished product work belongs only on
tickets. Two branches adding features add separate files, avoiding an index
merge conflict. Write what the product can do first: the heading, `Route:`, opening paragraph,
`Sub-features`, and `How to get to it (user POV)`. For a UI prototype, write this
before design freeze and commit it before tests on the effort branch or
`fix-<n>`. Take sentences only from the winner prototype, closed decisions, and
`CONTEXT.md`. Each sentence has an identifiable source and describes something
the prototype can demonstrate. Write sentences in the product UI's language;
keep the prescribed headings in English. Do not ask the owner to confirm the
sentences. The owner confirms only the prototype.

When those sources disagree, decisions govern rules, the glossary governs names,
and the prototype governs appearance and interaction. Update a prototype that
lags behind decisions or names. A missing decision that changes the UI goes through Design a UI (`mmw-mode/playbooks/design-a-ui.md`), and its answer updates
the prototype. For existing behavior without a new prototype, describe the
current product. Until the feature lands, the project branch's feature map
contains only what the product currently does.

Write `Proof` before tests. Write `Tests:` and `Driving it with e2e` with their
tests in the same commit. Record `Gotchas` when generation, bug fixing, or
maintenance discovers them. All feature files are read-only at night.
Each feature file has these H2s, from the user's point of view.

| H2 | Holds |
| --- | --- |
| `Sub-features` | What the feature is made of, one line each |
| `How to get to it (user POV)` | Route, navigation, the account it needs |
| `Driving it with e2e` | The test files that pin it and the locators that matter |
| `Proof` | What the user sees and can accomplish |
| `Gotchas` | What reads as broken but is not; what the local app cannot do |

If the test lacks a precondition that it needs, the test reports a failure and
the reason goes in that feature's `Gotchas`; use the **test-audit** skill for the diagnosis.

The map is the project's maintained verification source. A proof that drives
one convenient entry point is incomplete when the map lists others.
