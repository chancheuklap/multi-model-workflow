# Harness guard

Whether the names a repository uses only to make itself drivable have stayed in the
places it is allowed to keep them is `<scripts>/harness-guard.py`; `<scripts>` is the
notation this skill's `SKILL.md` defines under **Resolve `<scripts>` once**. Reads of
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

Every text file the repository tracks or would track — `git ls-files --cached --others
--exclude-standard`, so a file that is there and not committed yet is judged and a file
`.gitignore` covers is not. Outside a git repository it walks the directory instead.
What the product wrote while the criteria ran — a log, a captured screenshot — is not
part of the repository and does not decide whether a commit is green.

`.mmw/target.json` supplies `harness_markers` (the leak strings), `leaves_machine`
(extra files allowed to hold those strings), and `stories` (the command whose named
files are story-service code, including a file at the repository root). Without
`harness_markers` as a list of strings, the guard refuses (exit 2).

## The criterion, in one shape

Written onto the ticket, run by a shell months later with no model between. The script
is named bare: `verify-ticket.py` puts `<scripts>` on the `PATH` of the shell that
runs the line (its `--tools`).

```
CHECK: harness-guard.py .
EXPECT: HARNESS OK
```

The one argument is the repository root, and a `CHECK:` line runs there, so it is `.`.
It sweeps the whole tree, so any ticket of a batch can turn it red; the batch's last
ticket carries it, and the contract ticket only delivers the guard (the `to-tickets`
skill's `references/cutting-interface-tickets.md`, **contract ticket**).

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
- `2`: the argument was not one directory (`usage: harness-guard.py <repository-root>`
  or `no such directory: <path>` on stderr), or `.mmw/target.json` is missing,
  unreadable, or does not declare `harness_markers` as a list of strings. The
  refusal names the fact it found and `target_config.py --check --repo <root>`
  (a `refusal.py` three-part).
