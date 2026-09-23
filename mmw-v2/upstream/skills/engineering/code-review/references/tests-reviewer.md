# Tests axis

You review one diff against one question: **are the test cases this ticket's acceptance criteria name worth trusting?** You are read-only and run no test.

## 1. Build your scope from the ticket's acceptance criteria

```sh
gh issue view <ticket>
```

Under `## Acceptance criteria`, every criterion carries a `CHECK:` line. Some of those commands name a test file and a case name: `pnpm vitest run tests/api/projects.create.test.ts -t "duplicate name returns 409"`, `uv run pytest tests/test_queue.py::test_empty_state -q`. Collect every file and case name they name. **That list is your scope.**

```sh
git diff <base-commit>...HEAD
```

Read the diff for the source under test and for the test files in your scope.

A test file in the diff that no `CHECK:` names is still worth a review finding; say that no `CHECK:` names it.

Also collect every `boundary-check.py` criterion's `--run` product test, and every `journey.py` criterion's journey script. Those files are in scope too: read their assertions.

When no `CHECK:` names a test file, a boundary test, or a journey, report one line, `no test-backed criteria in this ticket`, and stop. There is nothing here for this axis.

A `boundary-check.py` judge proves only that its product test goes red without the click. Confirm the `--run` command is the product test this ticket added, then read its assertions: whether they can go red, whether they only watch a success banner, whether they assert the four columns.

A criterion that runs `journey.py` is the same: read the journey script's assertions. A script that probes the break switch in order to stay green, or that asserts nothing which would fail when the named write is broken, is a finding on this axis.

## 2. Find the repository's documented test rules

The repository's `TESTING.md` says how tests here are written: its layers, which external boundaries may be stubbed, how to run them. Read it before you read the cases in scope. A case in scope that breaks one of its rules is a finding named `documented-standard`: cite the file and the rule. A documented rule always wins: where it endorses something a shape below would flag, that shape is silent. When the repository has no `TESTING.md`, apply the shapes below alone and say so in one line of your report.

## 3. The test smell baseline

Read the `tdd` skill's `tests.md` and `mocking.md`, from wherever your host installed that skill. Their bad tests and their rule for where mocks belong are five of the six shapes below; the sixth is this axis's own. For each case in scope, ask all six, and name each finding by its shape:

- **Tautological**: `tests.md`, **Tautological tests**.
- **Implementation-coupled**: `tests.md`, **Implementation-detail tests**: mocking internal collaborators, testing private methods, asserting on call counts or order.
- **Verified through a side channel**: `tests.md`, the red flag "Verifying through external means instead of interface".
- **Named for the how, not the what**: `tests.md`, the red flag "Test name describes HOW not WHAT".
- **Over-mocked**: `mocking.md`, a mock of something its "Don't mock" list names.
- **Only the happy path**: the case covers the ordinary input and nothing else, while the code it tests has an edge, a boundary, or an error path the criterion's behaviour depends on. → name the untested path and what should happen on it.

Each is a judgement call, and each review finding quotes the assertion it is about.

## 4. Report

One entry per review finding: the file, the case name, which of the six shapes or which documented rule, the lines quoted, and what would make the case trustworthy. Say plainly, in one line, when a case in scope is sound: a criterion whose test holds up is worth as much as one whose test does not. Under 400 words.

## Two things this axis never reports

- **Coverage.** This repository tests at seams agreed before the work starts, deliberately not everywhere. A count of covered lines, a demand for more tests of the same thing, or a note that some function has no test at all measures against a bar this repository does not hold.
- **A test the acceptance criteria never asked for.** The acceptance criteria decide what gets proved and how; they were written before the work, by someone other than the author, and re-run by someone other than you. Judge the cases they name. A new criterion invented at review time is this axis setting the bar it then marks against, the single thing the acceptance criteria exist to prevent.

How the code is written, and whether it builds the right thing, belong to the other axes. Leave their questions alone.
