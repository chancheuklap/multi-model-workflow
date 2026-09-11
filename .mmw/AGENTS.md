# .mmw

This repository's own acceptance runtime: `target.json` names the local task board as the product, `harness/` starts and stops it behind a fake `gh`, `stories/` serves its component stories, `journeys/` holds the whole-product journeys. The scene data lives outside, in `prototypes/board-orchestration/task-board/UI/work/scenes.json`, the handoff package the screen contract's `baselines.look` names.

## Key Conventions

- `harness/target.py` runs only under a lease: without `MMW_DATA_DIR` and `MMW_PORT_BASE` it refuses and points at `lease.py run --`. `start` is idempotent (0 when the recorded pid still runs the same `server.py` at the same origin with the same token, otherwise it stops the old one first) and names the holder through `lsof` when something else has the port.
- `start` prepends `harness/bin` to the board's `PATH` and points `MMW_HOST_CATALOG` at `harness/catalog.json` (`{"hosts": {}}`): under automation the board talks to the fake `gh` and shows no host in the settings sheet. A criterion that expects a host there starts by changing that catalog.
- The fake `gh` looks up the exact compact JSON of its argument array in `harness/github/responses.json`; keys keep `{owner}` and `{repo}` literally because the board hands those placeholders to `gh` to expand. The second comments read answers 304 (exit 1, `gh: HTTP 304` on stderr) so a journey walks the production conditional-request path.
- `journeys/<name>/run` is started by `journey.py`, which uppercases every key `discover` prints into the environment (`smoke.py` reads `ORIGIN` and `INSTANCE_TOKEN` from there). Every journey runs a second time with the ports closed and `MMW_JOURNEY_NEGATIVE=1`, and that pass must fail, else the run reports `JOURNEY GREEN WITHOUT PRODUCT`.
- `stories/serve.py` serves the shipped modules from `mmw-v2/board/page/` under `/product/`, so a story renders production code; `stories/story.mjs` swaps the API layer for a stand-in that records `{method, path, fields}` and answers 200 with an empty body, exposed as `window.storyCalls()`, which the board's call tests assert against.

## Gotchas

- An unregistered call makes the fake `gh` exit 2 with `no gh response …; add that exact call before rerunning`: one changed argument order, flag or GraphQL string in how the board calls `gh` breaks every journey until `responses.json` is updated. It also refuses without `MMW_DATA_DIR`, since every call is appended to `$MMW_DATA_DIR/gh-calls` first.
- `stories/serve.py` exits 2 without `MMW_PORT_BASE` ("run through story-parity.py") and always listens on `MMW_PORT_BASE + 1`, one above the board. A `?page=` with no `stories/adapters/<page>.mjs` is a 404: the adapters are `topbar`, `tasks`, `canvas`, `detail`, `settings`, and the App page has none.
- `target.json` has no `checks` key, and its `leaves_machine` declares the one thing that leaves the machine: the board reading GitHub through `gh`.
