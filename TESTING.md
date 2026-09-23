# Testing

The rules for this repository's tests. The reviewer's Tests axis applies them; a ticket carries the ones that shape its work. The commands that run the tests are in `AGENTS.md` `## Commands`.

## Layout

- A skill's tests live in `mmw-v2/tests/<name>/`, which exists only in a checkout and climbs two levels to `mmw-v2/` and down into `skills/<name>/scripts/` to reach the script under test. The one exception is `mmw-v2/skills/verify-ticket/scripts/gate-check/`: it holds only relative symlinks to `gate-check.mjs`, `gate-lint.mjs` and `lib` in `mmw-v2/upstream-unlazy/scripts/`, and gate-check's tests are unlazy's own, in that subtree.
- `MMW_V2_HOME` is a test seam for `install.sh` only: it moves the whole install target to a throwaway directory and skips `launchctl` and `paseo reload`. Runtime configuration goes through `MMW_HOME`.

## Which suites a change needs

- The task board imports verify-ticket's `events.py` and `issue_tree.py` and dispatch's `ghlist.py` and `models.py` by file path (`mmw-v2/board/board_data.py`, `settings_api.py`), and `retro.py` loads `events.py` and `issue_tree.py` the same way; a change to them is a change to the board and the retro. Run `mmw-v2/tests/board/run.sh` together with the `relay` and `retro` suites.
