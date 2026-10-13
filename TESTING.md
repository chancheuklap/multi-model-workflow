# Testing

How this repository's tests run. Whoever writes a spec or a ticket draws the seam from it, and the review's Tests axis reads it as facts. The rules for what makes a good test are in the principles, not here.

## Where the tests live, and their layers

- A skill's tests live in `mmw-v4/tests/<name>/`, which exists only in a checkout and climbs two levels to `mmw-v4/` and down into `skills/<name>/scripts/` to reach the script under test. gate-check's own tests are in `mmw-v4/tests/verify-ticket/gate-check/`, and the `verify-ticket` suite runs them. The prompt renderer's tests are in `mmw-v4/prompt/tests/`.
- The install tests live in `mmw-v4/tests/install/test_install.py`; they need `mmw-v3/` beside `mmw-v4/`, because `--back` and the takeover of a v3 machine run its `install.sh`.
- `mmw-v4/tests/lib/` holds the three shared checks every suite runs first (`check_module_paths.py`, `check_wiring.py`, `check_skill_frontmatter.py`), and its own `run.sh` tests `check_wiring.py`.
- Four layers:
  - **unittest** (`test_*.py`): a script loaded as a module by its file path and called with fixed input (`mmw-v4/tests/verify-ticket/_load.py` loads `verify-ticket.py` and `events.py` this way).
  - **end to end** (`test_*.sh`, and the `test_*.py` that run a script as a process): the real script run as a process, with the external boundaries below replaced by fakes (`mmw-v4/tests/dispatch/test_dispatch.sh`, `mmw-v4/tests/relay/test_relay.sh`, `mmw-v4/tests/liveness/test_guard.sh`, `mmw-v4/tests/install/test_install.py`, `mmw-v4/tests/design-pages/test_pull_design.py`).
  - **node** (`*.test.mjs` under `mmw-v4/tests/board/`, and gate-check's `run-tests.mjs` and `lint-tests.mjs`): the board's page modules and gate-check's engine.
  - **browser**: the board suite drives the real board in a headless Chromium through Playwright.
- `check-interfaces.py`, beside `dispatch.sh`, checks that the dispatcher's side and the agent's side of every role meet; the dispatch suite's `test_check_interfaces.py` tests the checker itself.

## How to run them

- One suite: `bash mmw-v4/tests/<name>/run.sh`; the prompt renderer's: `bash mmw-v4/prompt/tests/run.sh`. There is no aggregate runner of the suites; `scripts/check` runs the ones a change needs, and `scripts/check --all` every one. Each `run.sh` header names what it tests and the tools it needs; every suite needs `uv` for the shared frontmatter check.
- A passing suite's last line is `all passed` (`全过` for `exe-release`).
- `design-pages`, `diagram-design` and `verify-ticket` take `-k <pattern>`, the substring or glob `python3 -m unittest -k` accepts (`mmw-v4/tests/lib/parse_k.sh`); under `-k` the `verify-ticket` suite skips its node half. `setup-mmw` takes a bare name pattern.
- One dispatch scenario: `bash mmw-v4/tests/dispatch/test_dispatch.sh <scenario>`, `all` for every one; its header lists them, and a passing scenario's last line is its EXPECT string. `mmw-v4/tests/relay/test_relay.sh` takes the same argument.
- `python3 mmw-v4/skills/dispatch/scripts/check-interfaces.py` prints `INTERFACES OK`.

## Stubbed boundaries

- **The tracker.** No test reaches GitHub. `test_dispatch.sh` and `test_relay.sh` put a fake `gh` on `PATH` that logs every call, one per line with fields joined by ` :: `; `test_dispatch.sh`'s answers from environment variables and a JSON file of ticket rows (`FAKE_GH_TICKETS_FILE`). The board suite has its own fake under `mmw-v4/tests/board/github/`; the task board's harness answers each exact call from `.mmw/task-board/harness/github/responses.json`. `mmw-v4/tests/setup-mmw/test_setup.py` answers every `gh` command, and every `git` command of `labels.py` and `check.py`, with a fake inside the test. The verify-ticket suite runs against fixed ticket bodies, and `_load.py` makes `ticket_spec` answer `None`, so no module it loads asks the tracker which spec a ticket sits under.
- **Claude Design's preview server.** `mmw-v4/tests/design-pages/test_pull_design.py` starts a local fake that serves project files and the three runtime scripts.
- **The runners.** `test_dispatch.sh` puts fake `paseo`, `herdr` and `orca` on `PATH`, each logging every call. `test_relay.sh` delivers through the real `runners/paseo.sh` adapter to a fake `paseo`. The liveness unit tests use a fake board and fake runner verbs. `mmw-v4/tests/dispatch/test_status.py` reads a fixed `paseo ls`/`inspect` snapshot.
- **The hosts' model catalogs.** `mmw-v4/tests/dispatch/catalog.json` and `catalogs/` stand in for each host's catalog.
- **The machine's install targets.** `test_install.py` puts fake `orca`, `nmem`, `paseo` and `launchctl` on `PATH`.
- **What runs for real:** git (bare origins and clones made in a temporary directory), processes and the state directory's locks (`statedir.py`'s lock is tested against real processes, a recycled pid among them), `node`, and the headless Chromium (board and design-pages suites).

## How a test puts the system into a state

- **Machine state.** Every suite that touches it points `MMW_HOME` at a temporary directory (`mmw-v4/tests/board/run.sh`, the relay and liveness suites, `test_dispatch.sh`'s `$TMP/mmw-home`); none touches `~/.mmw`. `MMW_INSTALL_HOME` is a test seam for `install.sh` and `render.py` only: it moves the whole install target to a throwaway directory and skips `launchctl` and `paseo reload`.
- **A repository.** `test_dispatch.sh` makes a bare `origin.git` and a clone under `mktemp -d`, and remakes them for a scenario that needs a fresh pair. `test_setup.py` moves an effort's files in a temporary git repository.
- **A ticket's history.** `_load.py`'s `event` writes a comment the way the pipeline's scripts post one, and `checked` writes one `ticket.checked` event; the fake `gh` serves ticket rows from `FAKE_GH_TICKETS_FILE`.
- **An open night.** Every `test_dispatch.sh` scenario runs with the night on spec 76 open: a stand-in process holds the relay's lock in the run's state directory and records that it watches spec 76. A scenario about opening, acking or refusing clears it first (`no_relay`).
- **A broken skill set.** `test_check_wiring.py` and `test_check_interfaces.py` run on a copy of `mmw-v4/skills/` broken one way per case; the `diagram-design` suite edits the skill's shipped example pages one way per case.
- **The board's data.** The board suite reads the design package's example data under `efforts/task-board/example-data/`; the task board's harness (`.mmw/task-board/harness/target.py`) starts the real board under a lease, with a private `MMW_HOME` seeded from `hosts.json`.

## Traps

- A suite runs from inside a runner's session as easily as from a terminal. `test_dispatch.sh` and the board suite unset `PASEO_AGENT_ID`, `ORCA_TERMINAL_HANDLE`, `HERDR_PANE_ID` and every `NMEM_*` variable first: a scenario says which session it stands in, and nothing else may answer `self`.
- A skip is a failure. `mmw-v4/tests/lib/run_unittests.py` exits 1 on a skip count other than 0 or a run count of 0, and the suite then withholds `all passed`; the `verify-ticket` suite fails without `node` rather than passing on half its tests.
- The task board loads verify-ticket's `events.py` and `issue_tree.py` and dispatch's `ghlist.py`, `models.py`, `statedir.py` and `roles.json` by file path (`mmw-v4/board/codeversion.py` lists them): a change to one of them is a change to the board.
- The board suite and `.mmw/task-board/harness/` read two scripts of `mmw-v3/skills/ui-acceptance/`, which v4 does not carry.
- The board and design-pages suites need Playwright's browsers. With Playwright cached, the board suite runs `uv` offline.

## Which suites a change needs

The map from a changed path to the suites it needs is `MAP` in `scripts/check`, its only copy; `scripts/check` with no flag runs the suites it selects for the paths changed against the base.

## Tests written this way on purpose

- No test asserts the wording of a skill's `SKILL.md`, a playbook, a reference, a refusal, or a start prompt's standing sentences. Tests assert exit codes, the strings a program reads (event names and fields, labels, output tokens), the facts a behaviour produces (a number, a path, an issue number, a session id, the data rows of a prompt), and the effect on files, the tracker fake or git; a refusal is checked by its exit code, by what it did not do, and by the fact it names.
- The liveness suite does not prove that a real host calls the turn guard with the payloads it feeds, or honours its answer: that is checked by hand against each host and recorded in `turn-guard.py`'s header (`mmw-v4/tests/liveness/run.sh`).
- `exe-release`'s two PowerShell checks (`check-generated-powershell.sh`, `check-template-behaviour.sh`) are in no suite and no tier of `scripts/check`: they need a Windows build machine, and `scripts/check` names them on its `not run here:` line.
