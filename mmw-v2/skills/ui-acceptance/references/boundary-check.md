# Boundary check

Whether a control's click produces the behaviour its screen-contract row names is `<scripts>/boundary-check.py`. It does not start the product and it does not read a page. It runs the command it was given twice in this process's cwd: first as written, then with `MMW_NEGATIVE=1` in the environment and nothing else changed. The first pass must exit 0; the second must exit non-zero. A ticket that owns a row this check covers carries it for that row.

## The criterion, in one shape

The **boundary criterion** is the line written onto the ticket, run by a shell months later with no model between.

```
CHECK: boundary-check.py --run "<the product's test command, a file or a case>"
EXPECT: BOUNDARY OK <n>/<n>
```

`<n>` is how many `--run` flags were given. Commands that share a test file may share a criterion; `--run` may be repeated. `--run` takes one command, not a shell line: `&&`, `||`, `;` and `|` are refused.

## Selecting one row's test

One row's test is named after the row id, dots and hyphens turned to underscores: `detail.close` → `test_detail_close`. Row ids can be prefixes of one another (`detail.close`, `detail.close-event`), and a runner that selects by substring then picks both: `python -m unittest … -k test_detail_close` runs `test_detail_close` and `test_detail_close_event`. A `--run` meant for one row then passes on the other row's test when its own is missing or renamed, and the criterion judges the wrong row.

A `--run` that names one row's test selects it by a pattern anchored at both ends, so it matches that name and nothing longer:

- unittest: `-k '*.test_detail_close'`. A `-k` value holding `*` is matched against the whole test name (`module.Class.test_detail_close`), so the leading `*.` and the missing trailing `*` match only a name ending in exactly `.test_detail_close`.
- pytest: the node id, `tests/test_rows.py::test_detail_close`, which names one test exactly.
- A runner whose filter is a regular expression: `^…$` around the name.

The command is run by hand twice. Before the criterion is published, whoever cuts the ticket runs it with the name changed to one no test has, which must exit non-zero. unittest exits 5 and prints `NO TESTS RAN` when a pattern selects nothing. A runner that exits 0 when its filter selects nothing turns a renamed test into a `MISS` only if the command is changed to fail on zero tests; find its flag for that before relying on it. Once the worker has written the test, the worker runs the command as written, which must report exactly one test run.

## The four-column boundary test

A **four-column boundary test** is the product's own test that asserts all four behaviour columns of one screen-contract row in the same test. This is what the criterion above runs.

The outbound call module is the layer the consuming repository names as the one that emits outbound calls, whether they travel as HTTP, IPC, or an extension message.

One test asserts the four columns of one screen-contract row:

- `calls`: the request and parameters the click emitted.
- `shows`: that module returns a marked value; the page displays that value.
- `next`: the page entered the state or scene `next` names.
- `on_failure`: that call returns failure; the page shows the failure the contract wrote.

A row whose `calls` is `none` and whose `next` is not `stay` still has one test: the click emits no outbound call and the page enters that `next`.

The consuming repository's contract ticket delivers one shared interaction helper (click, fill). Tests call only that helper, never the page directly; the helper finds the control by its `data-ui` id. Under `MMW_NEGATIVE=1` the helper does nothing. A control repeated in a list shares one id, so the helper also takes `<id>#<n>`, the n-th element with that id in document order counted from 1, the name the story judge gives repeated ids; a bare id is the first. A row about choosing one item of a list (a task, a card) clicks one the starting scene has not already chosen, or its assertion holds without the click.

The test replaces the outbound call module with a mock. Mocking that module is the allowed seam. Stubbing `fetch`, msw, nock or fetch-mock is not allowed. `verify-ticket.py --lint` reports `ERROR` when those names appear on a `CHECK:` line; a stub inside a test file is not that line, so lint does not catch it.

A cross-component row (`App · ` page, an action in region A that affects region B) is asserted at the whole-page composition: the request carries the other region's state, and the other region enters the scene the row names. The same `boundary-check.py` runs it; the negative control is the same.

The helper and the mock together make the second pass mechanical. Skip the click, and a test that really asserted those columns goes red; a test whose assertion is true without the click stays green, and this judge prints that.
