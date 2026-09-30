# mmw-v2/board

The task board's source: `server.py` serves one repository's board on 127.0.0.1, `supervisor.py` keeps one running per repository registered in `~/.mmw/boards.json`, plus `board_data.py`, `gates.py`, `settings_api.py` and the `page/` front end. It is a second store for nothing: ticket state is read from GitHub, model configuration read and written in `~/.mmw/models.json`.

## Key Conventions

- The task board loads `events.py`, `issue_tree.py`, `ghlist.py`, `models.py` and `statedir.py` through `locations.py`. `codeversion.py` finds that file at `mmw-v2/skills/mmw/scripts/locations.py` and, only when that file is absent, at `mmw-v2/skills/dispatch/scripts/locations.py`. `board_data.py`, `settings_api.py` and `supervisor.py` then load those scripts from the paths it registers. A change to them runs the board tests too.
- The page token is minted at every server start, injected by replacing the literal `__MMW_PAGE_TOKEN__` in `page/index.html`, and read back from `<meta name="mmw-page-token">`; this repository's product answers in the root `.mmw/` use that meta tag as their liveness proof and instance check.
- Every board process restarts itself onto new code: `codeversion.py` fingerprints `board/*.py`, `locations.py` and the scripts resolved through it, and when that fingerprint changes (two reads in a row agreeing) a `server.py` exits for the supervisor to start again and `supervisor.py` stops its servers and `execv`s itself with the same pid. Moving the installed checkout to a new commit is therefore the whole update; `page/` is read per request and needs no restart. A script the board loads is registered in `locations.py`.
- `supervisor.py` keeps its registry in `~/.mmw/boards.json` (mode 0600), allocating ports upward from 47100 under a lock and refusing a port anything already answers on; `--register` reserves the port, `--ensure` starts the server and waits up to ten seconds, and a server that does not come up is explained in `~/.mmw/board.log`.

## Gotchas

- `server.py` imports `board_data`, `codeversion`, `gates` and `settings_api` by bare name: run it as a script, or put this directory on `sys.path` before importing it.
- `gates.py` rejects every non-GET request whose `Host`, `Origin` and `X-MMW-Token` do not all match: a plain `curl` at a write endpoint gets 403.
- The supervisor prints `skipping missing repository …` once for a registered directory that is gone and stays silent until it returns, so a stale `boards.json` entry makes no further noise.
