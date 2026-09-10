# Task board prototype (#318)

## Question

What does the task board of #318 show and how does it respond: which lamp, pill and line each ticket gets from its fold, how a task's tree is laid out on the canvas, and what the detail panel says about each kind of card?

## Current conclusion

Settled in the interactive mockup and written into #318 sections 3 to 7 (the board) and 11 to 17 (reading GitHub, and the settings sheet): three columns (tasks, canvas, detail); a vertical trunk of containers that open to the right into their issues; one lamp answering "does this need me" (orange needs you, green running, ink done, hollow not dispatched); one pill naming the current step; blocking drawn as smooth curves coloured by how the wait stands (grey walked, green with a travelling light where the blocked ticket is running, red where the blocker has not landed).

The design is ported into Claude Design as five components (the four regions of the board and the settings sheet of #318 sections 12 to 17), one app page and an overview, bound to the `MMW Task Board` design system built from the repository's `DESIGN.md`:

- Project: https://claude.ai/design/p/457777fa-6ee0-43e9-85f1-e78e457f0629
- Design system: https://claude.ai/design/p/1d871e1b-2359-439c-a986-37e5657993f6

Not yet a baseline: #318 section 2 needs the handoff package brought back into this directory and a screen contract written from it by `align-screens`.

## Which parts the real code has taken

None.

## Layout

- `mockup/task-board-mockup.html` — the single-file mockup the port started from; open it in a browser. The gear at the right end of the top bar opens the settings sheet of #318 sections 12 to 17: dropdowns that choose, on this machine, the runner and each agent's host, model and effort. It is MMW's one place for that configuration: its options are what MMW gets by asking this machine's hosts' CLIs, a new machine starts from MMW's initial values, and a save reaches the next agent that starts. Its options are asked of Paseo when the runner is paseo and of each host's own CLI otherwise, the place `start` asks, so changing the runner to or from paseo scans again. While the sheet is open the scene bar steps through its own five scenes. Beside the read time, the refresh button reads GitHub at once; the page otherwise reads it every minute while it is open.
- `mockup/build_fixtures.py` — builds the example data with the pipeline's own event code: every event is written with `events.build` of the verify-ticket skill, with the first lines and fields `dispatch.sh` and `verify-ticket.py` write, and each ticket's state is `events.fold` of those comments. It writes the data into the mockup and into `work/data/fixtures.js`, and copies the mockup's board logic into `work/data/fixtures.js` so the two show a fold the same way. It also writes the settings sheet's data into both files, and copies the mockup's settings logic (`LocalConfig`, between the `SETTINGS-LOGIC` markers) into `work/data/fixtures.js` the same way; the data is built with the dispatch skill's `models.py`: hosts, their CLI binaries and default rows from `hosts.json`, runners from the adapters under `scripts/runners/`, and each host's model and effort options from `fillable_rows` over an example catalog shaped like what `scan_cli_catalogs` gets from the hosts' CLIs. Run it after changing a ticket, or after `events.py`, `models.py` or `hosts.json` changes: `python3 mockup/build_fixtures.py`.
- `mockup/check-fixtures.js` — checks what no single event can: the order of events across a ticket and across the tickets of a spec — no ticket dispatched before its blockers land or left undispatched once they have, every result through the closing steps of `implement` in order, a pass only on a reverify that is `met`, a hand-back only for `failed` or `stuck`, children routed only on the closing pass, nothing after a fault. Run it after every build: `node mockup/check-fixtures.js mockup/task-board-mockup.html`.
- `work/` — the port. `src/<name>.py` builds each `Component · <name>.dc.html` with `mk.py`; `App · 任务板.dc.html` and `Overview.dc.html` are written by hand; `styles/` and `data/fixtures.js` are loaded by every page. `data/fixtures.js` carries the example data, the scene tables of every component, and the board's logic (a ticket's fold in, canvas layout and panel views out). `data/fixtures.js` also carries the settings sheet's data and logic (`SETTINGS`, `LocalConfig`) and its component scenes; the App page opens the sheet from the gear and its `settings` prop opens it on one data scene.
- `work/serve.sh` holds a preview token and is ignored by git.

Rebuild a component after editing its source, from `work/`:

```
DC_FX=FIXTURES DC_FRAME=864x848 python3 mk.py "src/Component · 画布.py"
```

Frames: 顶栏 `1440x52`, 任务列表 `236x848`, 画布 `864x848`, 详情 `340x848`, 本机配置 `1440x900`.
