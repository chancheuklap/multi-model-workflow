# Boundary check

Whether a control's click produces the request its screen-contract `calls` column names is `<scripts>/boundary-check.py`; `<scripts>` is the notation this skill's `SKILL.md` defines under **Resolve `<scripts>` once**. It does not start the product and it does not read a page. It runs the command it was given twice in this process's cwd: first as written, then with `MMW_NEGATIVE=1` in the environment and nothing else changed. The first pass must exit 0; the second must exit non-zero. A ticket that owns a `calls` row carries this check for that row.

## The criterion, in one shape

Written onto the ticket, run by a shell months later with no model between. The script is named bare: `verify-ticket.py` puts `<scripts>` on the `PATH` of the shell that runs the line (its `--tools`).

```
CHECK: boundary-check.py --run "<the product's test command, a file or a case>"
EXPECT: BOUNDARY OK <n>/<n>
```

`<n>` is how many `--run` flags were given. Commands that share a test file may share a criterion; `--run` may be repeated. `--run` takes one command, not a shell line: `&&`, `||`, `;` and `|` are refused.

## What the product's test must do

The consuming repository's contract ticket delivers one shared interaction helper (click, fill) and the tests call only that helper, never the page directly. Under `MMW_NEGATIVE=1` the helper does nothing. The test asserts the request the product's API client module emitted — method, path, and fields — and replaces that module with a mock. Mocking the product's own API client module is the allowed seam. Stubbing `fetch`, msw, nock or fetch-mock is still a cheat. `verify-ticket.py --lint` reports `ERROR` when those names appear on a `CHECK:` line; a stub inside a test file is not that line, so lint does not catch it. This section and code review are what hold the test-file half.

That pairing is what makes the second pass mechanical. Skip the click, and a test that really asserted a request goes red; a test whose assertion is true without the click stays green, and this judge prints that.

## Why the second pass is not optional

An assertion that does not depend on the click reads exactly like one that does: both exit 0, both print a pass. The question a gate is judged by is whether a run that did nothing at all would be noticed (`docs/adr/0008-silence-is-never-a-pass.md`). The second pass is that notice. A reviewer does not read the test to decide whether it can go red; the judge writes `GREEN WITHOUT INTERACTION` when it cannot.

## Exit codes

- `0`, one line `BOUNDARY OK <n>/<n>`: every command exited 0 as written and non-zero with `MMW_NEGATIVE=1`.
- `1`, `MISS <command> — <last 20 lines of that command>` and then `Fix the product's test; the negative control was not reached.`: the first pass was already red; the product's test is failing on its own, before any negative control.
- `1`, `GREEN WITHOUT INTERACTION <command> — <why>. Make the assertion fail when the interaction helper does nothing.`: the first pass passed, and so did the pass that skipped the click. The assertion does not depend on the interaction.
- `2`: the command could not be started. The refusal names the fact it checked — unclosed quotes, an empty `--run`, a shell token, a missing executable, a file that could not be executed — and gives the one way out.

What to fix is what the line names. A `MISS` is the product's test. `GREEN WITHOUT INTERACTION` is an assertion that stays true when the helper does nothing.
