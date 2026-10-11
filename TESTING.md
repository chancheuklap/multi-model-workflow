# Testing

The rules for this repository's tests. The reviewer's Tests axis applies them; a ticket carries the ones that shape its work. The commands that run the tests are in `AGENTS.md` `## Commands`.

## What a test proves

A test proves what a script does, never what a piece of text says. Pinning the wording of a skill's `SKILL.md`, a playbook, a reference, a refusal, or a start prompt's standing sentences forces a test edit every time that text improves, and the passing test still proves nothing about behaviour. Assert exit codes, the strings a program reads (event names and fields, labels, output tokens), the facts the behaviour produces (a number, a path, an issue number, a session id, the data rows of a prompt), and the effect on files, the tracker fake, or git. A refusal is checked by its exit code, by what it did not do, and by the fact it names; its prose is not asserted.

## Layout

- A skill's tests live in `mmw-v4/tests/<name>/`, which exists only in a checkout and climbs two levels to `mmw-v4/` and down into `skills/<name>/scripts/` to reach the script under test. gate-check's own tests are in `mmw-v4/tests/verify-ticket/gate-check/`, and the `verify-ticket` suite runs them.
- The install tests live in `mmw-v4/tests/install/test_install.py`, with fake `orca`, `nmem`, `paseo` and `launchctl` on `PATH`; they need `mmw-v3/` beside `mmw-v4/`, because `--back` and the takeover of a v3 machine run its `install.sh`.
- `MMW_INSTALL_HOME` is a test seam for `install.sh` only: it moves the whole install target to a throwaway directory and skips `launchctl` and `paseo reload`. Runtime configuration goes through `MMW_HOME`.
- `mmw-v4/tests/lib/` holds the three checks every suite runs first, and its own `run.sh` tests `check_wiring.py` on copies of `mmw-v4/skills/` broken one way per case.

## Which suites a change needs

- The task board loads verify-ticket's `events.py` and `issue_tree.py` and dispatch's `ghlist.py`, `models.py`, `statedir.py` and `roles.json` by file path (`mmw-v4/board/codeversion.py` lists them); a change to them is a change to the board. Run `mmw-v4/tests/board/run.sh` together with the `relay` suite.
- A change to `roles.json`, `hosts.json`, a playbook's route or steps, the relay's wakes or `RESUME_STEPS` runs `check-interfaces.py`; the dispatch suite's `test_check_interfaces.py` covers the checker itself.
