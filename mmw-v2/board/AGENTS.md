# mmw-v2/board

The task board's source: `server.py` serves one repository's board on 127.0.0.1, `supervisor.py` keeps one running per repository registered in `~/.mmw/boards.json`, plus `board_data.py`, `gates.py`, `settings_api.py` and the `page/` front end. It is a second store for nothing: ticket state is read from GitHub, model configuration read and written in `~/.mmw/models.json`.

## Key Conventions

- `board_data.py` loads verify-ticket's `events.py` and `tree.py` and dispatch's `ghlist.py` by file path, and `settings_api.py` adds dispatch's `scripts/<…>` directory to `sys.path` and imports `models`: the board is downstream of those four scripts, and a change to them runs the board tests too.
- The page token is minted at every server start, injected by replacing the literal `__MMW_PAGE_TOKEN__` in `page/index.html`, and read back from `<meta name="mmw-page-token">`; the acceptance runtime uses that meta tag as its liveness proof and instance check.
- `supervisor.py` keeps its registry in `~/.mmw/boards.json` (mode 0600), allocating ports upward from 47100 under a lock and refusing a port anything already answers on; `--register` reserves the port, `--ensure` starts the server and waits up to ten seconds, and a server that does not come up is explained in `~/.mmw/board.log`.

## Gotchas

- `server.py` imports `board_data`, `gates` and `settings_api` by bare name: run it as a script, or put this directory on `sys.path` before importing it.
- `gates.py` rejects every non-GET request whose `Host`, `Origin` and `X-MMW-Token` do not all match: a plain `curl` at a write endpoint gets 403.
- The supervisor prints `skipping missing repository …` once for a registered directory that is gone and stays silent until it returns, so a stale `boards.json` entry makes no further noise.
