# Harness guard

Whether the names a repository uses only to make itself drivable have stayed in the
places it is allowed to keep them is `<scripts>/harness-guard.py`. Reads of
`MMW_` variables, and the strings `.mmw/target.json`'s `harness_markers` lists, may
appear in `.mmw/`, `tests/`, `scripts/dev/`, a test file kept beside the code it tests
(a path segment `__tests__` or `__mocks__`, or a name ending `.test.<ext>` or
`.spec.<ext>`), and the files `leaves_machine` names. Anywhere else is a leak: it is a
back door opened for automated acceptance that ships to a customer's machine with the
release. `[]` is a legal answer: this product has no such strings. A missing key is
not a default.

Story-service files — everything under `.mmw/stories/`, and files the `stories`
command names — may reference `scenes.json` and must not reference `.dc.html`.

## What it reads

Every file git tracks or would track is judged, committed or not; what the product wrote
while the criteria ran is not part of the repository.

## The criterion, in one shape

Written onto the ticket, run by a shell months later with no model between.

```
CHECK: harness-guard.py .
EXPECT: HARNESS OK
```

The one argument is the repository root, and a `CHECK:` line runs there, so it is `.`.

What widens the allowed set for one file is `.mmw/target.json`'s `leaves_machine`, never
an exception written into the check and never a name assembled at run time to get past it
(`process.env["MMW_" + "NEGATIVE"]`): a check that is evaded reports nothing about the
leaks beside what evaded it.

## Exit codes

- `0`, one line `HARNESS OK`: no acceptance name appears outside the allowed places,
  and no story-service file names a `.dc.html`.
- `1`, one line `HARNESS LEAK <file>:<line>` per leak, and one line
  `HARNESS DESIGN PAGE <file>:<line>` per story-service file that names a `.dc.html`
  (the first such line in that file). Move a leak into `.mmw/`, `tests/` or
  `scripts/dev/`, or name the file in `leaves_machine` when what it does is a thing
  that reaches past this machine. A design-page hit is a story service rendering a
  design page: point it at `scenes.json` instead.
- `2`: a refusal naming what it found and the command that fixes it.
