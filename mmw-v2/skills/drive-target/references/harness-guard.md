# Harness guard

Whether the names a repository uses only to make itself drivable have stayed in the
places it is allowed to keep them is `<scripts>/harness-guard.py`; `<scripts>` is the
notation this skill's `SKILL.md` defines under **Resolve `<scripts>` once**. It walks
the repository and reads every text file it can. Reads of `MMW_` variables,
`/api/dev/`, `transport off` and `__stub` may appear in `.mmw/`, `tests/`,
`scripts/dev/`, and the files `leaves_machine` names. Anywhere else is a leak: it is
a back door opened for automated acceptance that ships to a customer's machine with
the release.

## The criterion, in one shape

Written onto the ticket, run by a shell months later with no model between. The script
is named bare: `verify-ticket.py` puts `<scripts>` on the `PATH` of the shell that
runs the line (its `--tools`).

```
CHECK: harness-guard.py .
EXPECT: HARNESS OK
```

The one argument is the repository root, and a `CHECK:` line runs there, so it is `.`.
The contract ticket carries this criterion; what widens the allowed set is
`.mmw/target.json`'s `leaves_machine`, never an exception written into the check.

## Exit codes

- `0`, one line `HARNESS OK`: no acceptance name appears outside the allowed places.
- `1`, one line `HARNESS LEAK <file>:<line>` per leak: move the code into `.mmw/`,
  `tests/` or `scripts/dev/`, or name the file in `leaves_machine` when what it does
  is a thing that reaches past this machine.
- `2`: the argument was not one directory. `usage: harness-guard.py <repository-root>`
  or `no such directory: <path>` says which, on stderr.
