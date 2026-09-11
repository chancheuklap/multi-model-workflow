# mmw-v2/tests

Every test of the toolbox's own scripts (the own-script layer), one directory per skill or subsystem; it exists only in a checkout and is never symlinked into a host. gate-check's own tests live beside gate-check, not here.

## Key Conventions

- Each directory's `run.sh` is run on its own; its header states what it tests and which runtime it needs. A new suite follows the same header.
- A test file climbs two levels to `mmw-v2/` and descends into `skills/<name>/scripts/`, loading the script under test by path with `importlib` (`verify-ticket.py` is no identifier; `verify-ticket/_load.py` does that load, stubs `ticket_spec` to return `None` so no test reaches the tracker, and builds the event fixtures). `board/` climbs one level more, to the repository root, for `.mmw/` and `mmw-v2/board/`.
- A runner strips the session's identity from the environment before running: `MMW_TICKET`, `MMW_CATALOG_MODE`, `MMW_SPEC`, `MMW_KIND`, `MMW_EVENTS_PY`, `PASEO_AGENT_ID`; `dispatch/test_dispatch.sh` also strips `ORCA_TERMINAL_HANDLE` and `HERDR_PANE_ID` so only its fake runner answers `self`. A new `MMW_*` variable or a new runner joins this list, so that a suite run from inside a worker session leaves that session's real ticket alone.
- `MMW_HOME` isolation: `verify-ticket` and `drive-target` point it at a `mktemp -d` for the whole suite; `dispatch`, `relay` and `liveness` set it inside their test files; `board` sets it nowhere, so a new board test that reaches `models.py` or the supervisor sets its own or writes into the real `~/.mmw`.
- `dispatch` and `relay` scenarios run against fake `paseo`, `herdr`, `orca`, `launchctl` and `gh` in a temporary `bin`, each call logged one per line with ` :: ` between fields; a scenario passes when its last line equals its EXPECT string. Every dispatch scenario starts with a stand-in process holding the relay lock for spec 76; a scenario about `open` or `ack` releases it with `no_relay` first.
- The `exe-release` and `manage-agents-md` runners leave `set -e` off and grep each test's output for bash runtime faults (`unbound variable`, `command not found`, `syntax error near`, `integer expression expected`); a zero exit carrying one of those counts as a failure.
- No `verify-ticket` test needs a real judge on `PATH`: `test_judges_reachable.py` empties `PATH` to test the refusal and plants a one-line fake executable for the positive case. One of its cases is bound to the real drive-target scripts directory, so renaming a judge script turns it red.

## Gotchas

- `drive-target/run.sh` exits non-zero on any skipped test (`refusing: skipped 1`), and the suite skips a case when `node` is missing, so a machine with `uv` and no `node` goes red. `MMW_FORCE_SKIP=1` injects one skip to prove that rule. Chromium comes from `story-parity.py`'s own PEP 723 block, which is why `run.sh` asks only for numpy and Pillow.
- `verify-ticket/run.sh` runs two node suites (`run-tests.mjs`, `lint-tests.mjs`) and a missing `node` is a hard failure; `test_fenced_check.py` calls `node` directly. `claude-design-blocks` likewise: Python runs the unittests and Node executes the page's logic class, so a missing `node` fails the suite.
- `board/run.sh` starts one `uv run --with playwright` per `test_*.py` and one `node --test` per `*.test.mjs`; four cases launch a real headless Chromium, and `--with playwright` supplies only the Python package, so the browser is installed separately. The suite depends on the root `.mmw/` (`story_helper.py` starts `.mmw/stories/serve.py`, `test_harness.py` runs `.mmw/harness/bin/gh`), so a change to `.mmw/` shows up here.
- `board/github/gh` and `.mmw/harness/bin/gh` are two fake `gh` implementations and are not interchangeable: the first plays a `scenario.json` from `MMW_BOARD_FAKE_DIR` (`fail_all`, `fail_comments`, several tree versions, calls logged to `calls.jsonl`); the second answers from an exact-argument catalog.
- `dispatch/run.sh` changes into the tests directory before running `test_dispatch.sh`, because `dispatch.sh` asks git about the current checkout.
- `liveness/run.sh` proves the guard against fake host payloads only; that a real host calls the hook with that payload and honours its answer was checked by hand and is recorded in `turn-guard.py`'s header. `test_guard.sh` starts a real `watchdog.py` and kills it in its EXIT trap by the pid in the lock file; an interrupted run leaves one behind.
- The two PowerShell halves of `exe-release` cannot run on a Mac and are checked by hand against a build machine: `exe-release/check-generated-powershell.sh <machine> <release.ps1>` and `exe-release/check-template-behaviour.sh <machine>`. Passing syntax does not mean the guards judge correctly.
- `mmw-v2/prompt/tests/` isolates with `MMW_V2_HOME`, not `MMW_HOME`.

## Commands

| Command | What it does |
| --- | --- |
| `bash dispatch/test_dispatch.sh <scenario>` / `bash relay/test_relay.sh <scenario>` | One scenario by name; `all` runs every scenario |
| `MMW_FORCE_SKIP=1 bash drive-target/run.sh` | Expected to go red: proves the runner's no-skip rule still holds |
