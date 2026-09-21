# mmw-v2/tests

Every test of the toolbox's own scripts (the own-script layer), one directory per skill or subsystem, plus `lib/` for the `-k` parsing and unittest verdict four of those entries share; it exists only in a checkout and is never symlinked into a host. gate-check's own tests live in the `mmw-v2/upstream-unlazy/` subtree, not here.

## Key Conventions

- Each directory's `run.sh` is run on its own; its header states what it tests and which runtime it needs. A new suite follows the same header.
- `lib/` is not a suite: `-k` parsing (`parse_k.sh`) and the unittest verdict (`run_unittests.py`) for `ui-acceptance/run.sh`, `design-pages/run.sh`, `write-screen-contract/run.sh` and `verify-ticket/run.sh` live there. Each of those four still owns its runtime — ui-acceptance sets `MMW_HOME`, probes a port block, injects `MMW_FORCE_SKIP`, and runs under `uv run --with pillow`; design-pages runs under `uv run --with 'playwright>=1.58'`; write-screen-contract runs under `uv run --with pyyaml --with 'playwright>=1.58'` and its skeleton cases start a real headless Chromium.
- A test file climbs two levels to `mmw-v2/` and descends into `skills/<name>/scripts/`, loading the script under test by path with `importlib` (`verify-ticket.py` is no identifier; `verify-ticket/_load.py` does that load, stubs `ticket_spec` to return `None` so no test reaches the tracker, and builds the event fixtures). `board/` climbs one level more, to the repository root, for `.mmw/` and `mmw-v2/board/`.
- A runner strips the session's identity from the environment before running: `MMW_TICKET`, `MMW_CATALOG_MODE`, `MMW_SPEC`, `MMW_TASK_SCOPE`, `MMW_KIND`, `MMW_EVENTS_PY`, every `NMEM_*` variable, `PASEO_AGENT_ID`; a suite that tests judge ownership also strips `MMW_JUDGE_LEASE_OWNER`, so an outer acceptance run cannot make its inner judge skip cleanup; `dispatch/test_dispatch.sh` also strips `ORCA_TERMINAL_HANDLE` and `HERDR_PANE_ID` so only its fake runner answers `self`. A new `MMW_*` variable or a new runner joins this list, so that a suite run from inside a worker session leaves that session's real ticket and Memory boundary alone.
- `MMW_HOME` isolation: `verify-ticket` and `ui-acceptance` point it at a `mktemp -d` for the whole suite; `dispatch`, `relay` and `liveness` set it inside their test files; `board` sets it nowhere, so a new board test that reaches `models.py` or the supervisor sets its own or writes into the real `~/.mmw`.
- `dispatch` and `relay` scenarios run against fake `paseo`, `herdr`, `orca`, `nmem`, `launchctl` and `gh` in a temporary `bin`, each call logged one per line with ` :: ` between fields; the fake `nmem` also keeps JSON Space and Identity state. A scenario passes when its last line equals its EXPECT string. Every dispatch scenario starts with a stand-in process holding the relay lock for spec 76; a scenario about `open` or `ack` releases it with `no_relay` first.
- The `exe-release` and `manage-agents-md` runners leave `set -e` off and grep each test's output for bash runtime faults (`unbound variable`, `command not found`, `syntax error near`, `integer expression expected`); a zero exit carrying one of those counts as a failure.
- No `verify-ticket` test needs a real judge on `PATH`: `test_judges_reachable.py` empties `PATH` to test the refusal and plants a one-line fake executable for the positive case. One of its cases is bound to the real ui-acceptance scripts directory, so renaming a judge script turns it red.

## Gotchas

- `ui-acceptance/run.sh` exits non-zero on any skipped test (`refusing: skipped 1`). `MMW_FORCE_SKIP=1` injects one skip to prove that rule. Chromium comes from `story-parity.py`'s own PEP 723 block, which is why `run.sh` asks only for Pillow.
- `verify-ticket/run.sh` runs two node suites (`run-tests.mjs`, `lint-tests.mjs`) and a missing `node` is a hard failure; `test_fenced_check.py` calls `node` directly. `design-pages` runs its Python unittests under `uv` with Playwright and starts a real headless Chromium for pull fixtures; a missing `uv` or Chromium fails the suite.
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
| `bash ui-acceptance/run.sh -k <pattern>` / `bash design-pages/run.sh -k <pattern>` / `bash write-screen-contract/run.sh -k <pattern>` | Run only cases whose full unittest name matches the same substring or `*` pattern accepted by `python3 -m unittest -k`; a pattern that selects zero cases is a failure |
| `MMW_FORCE_SKIP=1 bash ui-acceptance/run.sh` | Expected to go red: proves the runner's no-skip rule still holds |
