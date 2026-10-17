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
- `mmw-v4/tests/register-problem/test_register.py` tests the registration command as a module and as a process. Its fake `gh` holds issues, labels, parents, closing links, and event comments. The concurrency case holds one fake issue read at a file gate until the test releases it, while a second registration runs. The tracker fixture locks each request rather than a whole registration. Git repositories, process identities, and locks run for real in temporary directories, with `MMW_HOME` pointing at the test home.
- `mmw-v4/tests/retro/test_retro.py` calls expire, gather, and apply as commands against a paginated fake `gh`, with a process case using that fake on `PATH`. Run histories and occurrences are event comments; `MMW_NOW` fixes their age. Gather runs against real temporary git commits and reverts. Fixed analyst answer tables drive apply without starting sessions, including a gather-to-apply case using the generated context. Write failures are injected after tracker mutations to test replay from the material directory's `.retro-apply` journal; comment markers prevent duplicate writes. `MMW_HOME` points at a test home.
- `mmw-v4/tests/writing-for-agents/` and `mmw-v4/tests/worktree-audit/` test the comparison and audit scripts as processes. The comparison fixtures commit baseline upstream and local copies, then updated upstream files, in real temporary repositories. The audit fixtures use a bare origin and clone with `dev` ahead of `main`, `origin/HEAD` pointing to `dev`, and a worktree merged into `dev`. Only `gh` is faked on `PATH`; neither suite reaches GitHub or the machine’s session records.
- `check-interfaces.py`, beside `dispatch.sh`, checks that the dispatcher's side and the agent's side of every role meet; the dispatch suite's `test_check_interfaces.py` tests the checker itself.

## How to run them

- One suite: `bash mmw-v4/tests/<name>/run.sh`; the prompt renderer's: `bash mmw-v4/prompt/tests/run.sh`. There is no aggregate runner of the suites; `scripts/check` runs the ones a change needs, and `scripts/check --all` every one. Each `run.sh` header names what it tests and the tools it needs; every suite needs `uv` for the shared frontmatter check.
- A passing suite's last line is `all passed` (`全过` for `exe-release`).
- `design-pages`, `diagram-design` and `verify-ticket` take `-k <pattern>`, the substring or glob `python3 -m unittest -k` accepts (`mmw-v4/tests/lib/parse_k.sh`); under `-k` the `verify-ticket` suite skips its node half. `setup-mmw` takes a bare name pattern.
- One dispatch scenario: `bash mmw-v4/tests/dispatch/test_dispatch.sh <scenario>`, `all` for every one; its header lists them, and a passing scenario's last line is its EXPECT string. `mmw-v4/tests/relay/test_relay.sh` takes the same argument.
- `python3 mmw-v4/skills/dispatch/scripts/check-interfaces.py` prints `INTERFACES OK`.

## Stubbed boundaries

- **The tracker.** No test reaches GitHub. `test_dispatch.sh` and `test_relay.sh` put a fake `gh` on `PATH` that logs every call, one per line with fields joined by ` :: `; `test_dispatch.sh`'s answers from environment variables and a JSON file of ticket rows (`FAKE_GH_TICKETS_FILE`). The board suite has its own fake under `mmw-v4/tests/board/github/`. `mmw-v4/tests/setup-mmw/test_setup.py` answers every `gh` command, and every `git` command of `labels.py` and `check.py`, with a fake inside the test. The verify-ticket suite runs against fixed ticket bodies, and `_load.py` makes `ticket_spec` answer `None`, so no module it loads asks the tracker which spec a ticket sits under.
- **Claude Design's preview server.** `mmw-v4/tests/design-pages/test_pull_design.py` starts a local fake that serves project files and the three runtime scripts.
- **The runners.** `test_dispatch.sh` puts fake `paseo`, `herdr` and `orca` on `PATH`, each logging every call. `test_relay.sh` delivers through the real `runners/paseo.sh` adapter to a fake `paseo`. The liveness unit tests use a fake board and fake runner verbs. `mmw-v4/tests/dispatch/test_status.py` reads a fixed `paseo ls`/`inspect` snapshot.
- **The hosts' model catalogs.** `mmw-v4/tests/dispatch/catalog.json` and `catalogs/` stand in for each host's catalog through `MMW_HOST_CATALOG`. `test_catalog.py` instead writes fake `claude`, `codex`, and `paseo` executables into a temporary `HOME/.local/bin`; they log calls and answer the control-request or app-server line protocol. Its missing-command case restricts the search folders so it cannot select a machine's real binary. `test_settings_api.py` reuses those host fakes to drive background reads through the real board process, and seeds `MMW_HOME/catalog.json` to test stored catalogs. Its `MMW_HOST_CATALOG` fixture uses `fixture-catalog.json`, separate from that cache.
- **The machine's install targets.** `test_install.py` puts fake `orca` (its setups in a JSON file the test writes), `gh`, `node`, `nmem`, `paseo` and `launchctl` on `PATH`; the case for missing base tools runs `--check` on a `PATH` of only `python3`, `uv`, `git`, the fake `gh`, `/usr/bin` and `/bin`.
- **What runs for real:** git (bare origins and clones made in a temporary directory), processes and the state directory's locks (`statedir.py`'s lock is tested against real processes, a recycled pid among them), `node`, and the headless Chromium (board and design-pages suites).

## How a test puts the system into a state

- **Machine state.** Every suite that touches it points `MMW_HOME` at a temporary directory (`mmw-v4/tests/board/run.sh`, the relay and liveness suites, `test_dispatch.sh`'s `$TMP/mmw-home`, and `test_status.py`'s `Plans.setUp`); none touches `~/.mmw`. `MMW_INSTALL_HOME` is a test seam for `install.sh` and `render.py` only: it moves the whole install target to a throwaway directory and skips `launchctl` and `paseo reload`.
- **A repository.** `test_dispatch.sh` makes a bare `origin.git` and a clone under `mktemp -d`, and remakes them for a scenario that needs a fresh pair.
- **Failed finish cleanup.** `test_dispatch.sh` uses a nonexistent local origin path, a real branch-reference lock on the night or project branch, or a bare-origin update hook that rejects deletion. The project-branch lock covers creation, an unchecked branch update, and a fast-forward in a checked-out worktree. A temporary git wrapper refuses only `git -C <repo> worktree list --porcelain`; its other commands use the real git binary. The retry removes that failure and runs `finish` against the same recorded merge.
- **A missing project worktree.** `test_dispatch.sh` deletes a fixture worktree directory without removing its git registration. It checks that `finish` names the missing path and gives inspection and pruning commands without pruning automatically, then prunes the fixture registration and retries.
- **Issue closing and reopening.** `test_dispatch.sh`'s fake `gh` records issue state changes in `gh-issue-states.json`, separate from the ticket rows. Later `gh issue view --json state --jq .state` reads those changes. A refused close changes nothing. `reset_log` clears the recorded states between scenarios.
- **A ticket's history.** `_load.py`'s `event` writes a comment the way the pipeline's scripts post one, and `checked` writes one `ticket.checked` event; the fake `gh` serves ticket rows from `FAKE_GH_TICKETS_FILE`.
- **Label migration.** `mmw-v4/tests/setup-mmw/test_setup.py` supplies issue pages, parents and comments through its fake `gh`; comment bodies are built with `events.py` and served as paginated REST objects. Label and issue edits update that same fake repository so retries and a second run observe the previous writes.
- **An open night.** Every `test_dispatch.sh` scenario runs with the night on spec 76 open: a stand-in process holds the relay's lock in the run's state directory and records that it watches spec 76. A scenario about opening, acking or refusing clears it first (`no_relay`).
- **A broken skill set.** `test_check_wiring.py` and `test_check_interfaces.py` run on a copy of `mmw-v4/skills/` broken one way per case. `test_status.py` copies the dispatch and verify-ticket scripts to a temporary skill tree with a missing or corrupt `roles.json`. The `diagram-design` suite edits the skill's shipped example pages one way per case.
- **The board's data.** The board suite starts the real `mmw-v4/board/server.py` through `mmw-v4/tests/board/board_process.py`, its fake `gh` answering from the test's fixture; a node test writes a page module's input inside the test.

## Traps

- A suite runs from inside a runner's session as easily as from a terminal. `test_dispatch.sh` and the board suite unset `PASEO_AGENT_ID`, `ORCA_TERMINAL_HANDLE`, `HERDR_PANE_ID` and every `NMEM_*` variable first: a scenario says which session it stands in, and nothing else may answer `self`.
- A skip is a failure. `mmw-v4/tests/lib/run_unittests.py` exits 1 on a skip count other than 0 or a run count of 0, and the suite then withholds `all passed`; the `verify-ticket` suite fails without `node` rather than passing on half its tests.
- The task board loads verify-ticket's `events.py` and `issue_tree.py` and dispatch's `ghlist.py`, `models.py`, `statedir.py` and `roles.json` by file path (`mmw-v4/board/codeversion.py` lists them): a change to one of them is a change to the board.
- The design-pages offline check waits up to 15 seconds for visible content, then observes another 3 seconds for asynchronous console errors, exceptions and requests. It cannot establish what happens after that observation window.
- The board and design-pages suites take the newest Playwright `uv` resolves (no pin, no upper bound: it follows global upgrades) and run `mmw-v4/tests/lib/ensure_chromium.py` first, which installs the Chromium build that Playwright needs when it is absent and never deletes another build. When Chromium still cannot start, the suite exits 2 before any test runs, and `scripts/check` reports it as `ENV` and ends `CHECK CANNOT RUN` rather than red. A suite's `run.sh` exits 2 for nothing else. With Playwright cached, the board suite runs `uv` offline, on the newest cached release.

## Which suites a change needs

The map from a changed path to the suites it needs is `MAP` in `scripts/check`, its only copy; `scripts/check` with no flag runs the suites it selects for the paths changed against the base.

## Tests written this way on purpose

- No test asserts the wording of a skill's `SKILL.md`, a playbook, a reference, a refusal, or a start prompt's standing sentences. Tests assert exit codes, the strings a program reads (event names and fields, labels, output tokens), the facts a behaviour produces (a number, a path, an issue number, a session id, the data rows of a prompt), and the effect on files, the tracker fake or git; a refusal is checked by its exit code, by what it did not do, and by the fact it names.
- The liveness suite does not prove that a real host calls the turn guard with the payloads it feeds, or honours its answer: that is checked by hand against each host and recorded in `turn-guard.py`'s header (`mmw-v4/tests/liveness/run.sh`).
- `exe-release`'s two PowerShell checks (`check-generated-powershell.sh`, `check-template-behaviour.sh`) are in no suite and no tier of `scripts/check`: they need a Windows build machine, and `scripts/check` names them on its `not run here:` line.

The design-pages `INJECTED_LIVE` fixture records the head injection measured on a real Claude Design project on 2026-09-21. `strip_injected_head` keeps that exact newline shape as well as whitespace-tolerant removal. A changed live injection shape must be measured again on a real project; the fake preview cannot establish it.
