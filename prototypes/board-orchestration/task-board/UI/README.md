# Task board prototype (#318)

## Question

What does the task board of #318 show and how does it respond: which lamp, pill and line each ticket gets from its fold, how a task's tree is laid out on the canvas, and what the detail panel says about each kind of card?

## Current conclusion

Settled in the interactive mockup and written into #318 sections 3 to 7: three columns (tasks, canvas, detail); a vertical trunk of containers that open to the right into their issues; one lamp answering "does this need me" (orange needs you, green running, ink done, hollow not dispatched); one pill naming the current step; blocking drawn as smooth curves coloured by how the wait stands (grey walked, green with a travelling light where the blocked ticket is running, red where the blocker has not landed).

The design is ported into Claude Design as four components, one app page and an overview, bound to the `MMW Task Board` design system built from the repository's `DESIGN.md`:

- Project: https://claude.ai/design/p/457777fa-6ee0-43e9-85f1-e78e457f0629
- Design system: https://claude.ai/design/p/1d871e1b-2359-439c-a986-37e5657993f6

Not yet a baseline: #318 section 2 needs the handoff package brought back into this directory and a screen contract written from it by `align-screens`.

## Which parts the real code has taken

None.

## Layout

- `mockup/task-board-mockup.html` — the single-file mockup the port started from; open it in a browser.
- `mockup/build_fixtures.py` — builds the example data with the pipeline's own event code: every event is written with `events.build` of the verify-ticket skill, with the first lines and fields `dispatch.sh` and `verify-ticket.py` write, and each ticket's state is `events.fold` of those comments. It writes the data into the mockup and into `work/data/fixtures.js`, and copies the mockup's board logic into `work/data/fixtures.js` so the two show a fold the same way. Run it after changing a ticket or after `events.py` changes: `python3 mockup/build_fixtures.py`.
- `mockup/check-fixtures.js` — checks what no single event can: the order of events across a ticket and across the tickets of a spec — no ticket dispatched before its blockers land or left undispatched once they have, every result through the closing steps of `implement` in order, a pass only on a reverify that is `met`, a hand-back only for `failed` or `stuck`, children routed only on the closing pass, nothing after a fault. Run it after every build: `node mockup/check-fixtures.js mockup/task-board-mockup.html`.
- `work/` — the port. `src/<name>.py` builds each `Component · <name>.dc.html` with `mk.py`; `App · 任务板.dc.html` and `Overview.dc.html` are written by hand; `styles/` and `data/fixtures.js` are loaded by every page. `data/fixtures.js` carries the example data, the scene tables of every component, and the board's logic (a ticket's fold in, canvas layout and panel views out).
- `work/serve.sh` holds a preview token and is ignored by git.

Rebuild a component after editing its source, from `work/`:

```
DC_FX=FIXTURES DC_FRAME=864x848 python3 mk.py "src/Component · 画布.py"
```

Frames: 顶栏 `1440x52`, 任务列表 `236x848`, 画布 `864x848`, 详情 `340x848`.
