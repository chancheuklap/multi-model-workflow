# Testing

Where this repository's tests live, what they need and how to run them. The reviewer's Tests axis applies these rules; a ticket carries the ones that shape its work.

## Layout

- A skill's tests live in `mmw-v2/tests/<name>/`, which exists only in a checkout and climbs two levels to `mmw-v2/` and down into `skills/<name>/scripts/` to reach the script under test. The one exception is `mmw-v2/skills/verify-ticket/scripts/gate-check/`: it holds only relative symlinks to `gate-check.mjs`, `gate-lint.mjs` and `lib` in `mmw-v2/upstream-unlazy/scripts/`, and gate-check's tests are unlazy's own, in that subtree.
- Some suites run under `uv run`; the verify-ticket and gate-check tests need `node`; the board, ui-acceptance, design-pages and write-screen-contract tests need Playwright's browsers.
- `MMW_V2_HOME` is a test seam for `install.sh` only: it moves the whole install target to a throwaway directory and skips `launchctl` and `paseo reload`. Runtime configuration goes through `MMW_HOME`.

## Commands

| Command | What it does |
| --- | --- |
| `bash mmw-v2/prompt/tests/run.sh` | Tests `render.py`; needs only `python3` |
| `bash mmw-v2/tests/<name>/run.sh` | One skill's or subsystem's suite, twelve of them: `verify-ticket`, `ui-acceptance`, `write-screen-contract`, `dispatch`, `retro`, `exe-release`, `manage-agents-md`, `design-pages`, `board`, `liveness`, `relay`, `migrations`. `advisor` and `code-checkers` have none. There is no aggregate runner; each `run.sh` header names what it tests and what runtime it needs (the `board` one does not: `uv`, Playwright and a real headless Chromium). Every `run.sh` first runs `mmw-v2/tests/lib/check_module_paths.py`, which fails when a script names a module file (`"<name>.py"`, `load("<name>")`) that no longer exists, then `check_upstream_em_dashes.py` beside it, which fails when a `.md` under `mmw-v2/upstream/skills/` has an em-dash outside a fenced code block |
| `bash mmw-v2/tests/dispatch/test_dispatch.sh <scenario>` | One dispatch scenario (about seventy; `all` runs them all); `mmw-v2/tests/relay/test_relay.sh` takes the same argument |
| `bash mmw-v2/hooks/tests/run.sh` | Tests `rule-at-moment.py`, a hook kept in the repository that `install.sh` leaves alone; whoever wants it registers it by hand under `~/.claude/hooks/` |
| `cd mmw-v2/upstream-unlazy/tests && node run-tests.mjs && node lint-tests.mjs` | gate-check's own tests, the two of unlazy's suites that cover what verify-ticket uses (the vendored layer); `verify-ticket`'s `run.sh` runs them too. unlazy's other suites there cover what this repository removed or does not use and are not run |

## Which suites a change needs

- The task board imports verify-ticket's `events.py` and `issue_tree.py` and dispatch's `ghlist.py` and `models.py` by file path (`mmw-v2/board/board_data.py`, `settings_api.py`), and `retro.py` loads `events.py` and `issue_tree.py` the same way; a change to them is a change to the board and the retro. Run `mmw-v2/tests/board/run.sh` together with the `relay` and `retro` suites.
