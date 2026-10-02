# Task board

The local browser page over the pipeline's work: one small HTTP server per registered consuming repository, reading that repository's ticket state from the tracker and reading or writing this machine's agent configuration. The command that opens it, `dispatch.sh board`, is defined in `docs/contexts/night/CONTEXT.md`. Every fact the page reads about a ticket, spec, map or decision — its number, title, events, blocking edges — is named by the term the other six contexts give it, in English. What belongs here is the page's own vocabulary: the names it coins for how it presents those facts, and for keeping what it shows current.

## Language

### The task board and what keeps it running

**task board**:
The local browser page for reading a spec's ticket state and editing this machine's `models.json`, served on `127.0.0.1` by one `server.py` per registered consuming repository. A model change goes through the same validation and write as `models.py config`.
_Home_: `mmw-v2/board/server.py`

**`boards.json`**:
The machine-level registry at `MMW_HOME/boards.json` mapping each consuming repository's **main worktree** path to its task board's fixed local port. It holds no ticket or model state.
_Home_: `mmw-v2/board/supervisor.py`

**`supervisor.py`**:
`mmw-v2/board/supervisor.py`, the process the `com.mmw.board` LaunchAgent keeps alive, which starts and restarts `server.py` for every repository `boards.json` registers.
_Home_: `mmw-v2/board/supervisor.py`

**page token**:
The secret `server.py` mints at every start and hands to the page, which sends it back as the `X-MMW-Token` header on every non-`GET` request. A write from another origin, a stale page or a bare `curl` is refused. This repository's own product answers read it from `<meta name="mmw-page-token">` as their liveness proof and instance check.
_Home_: `mmw-v2/board/server.py`, `.mmw/harness/target.py`

**`codeversion.py`**:
`mmw-v2/board/codeversion.py`'s `Watch`, which fingerprints `board/*.py` and the Python files the board loads through `locations.py` (when `locations.py` cannot be loaded, the bytes of its candidate files instead) and reports a change only once two reads agree: `server.py` exits on it for the supervisor to start it again, and `supervisor.py` stops its servers and re-`execv`s itself.
_Home_: `mmw-v2/board/codeversion.py`

### What the page shows

**page regions**:
The four areas of the task board page, each a `Component · ` page of the screen contract: the top bar (`顶栏`), the left column (`任务列表`), the canvas (`画布`) and the detail column (`详情`). The settings sheet (`本机配置`) is a dialog over them, not a region.
_Home_: `docs/specs/task-board/screen-contract.yaml`, `mmw-v2/board/page/app.mjs`

**Maps & specs**:
One row of the left column, and that column's title: a top-level map, or a spec no open map holds, together with the specs and tickets under it. A selected map's detail title is `Map`, and a selected spec's stays `Spec`. Distinct from a **night**, one run of one spec's tickets.
_Home_: `mmw-v2/board/page/tasks.mjs`, `mmw-v2/board/page/detail.mjs`

**lamp**:
The dot in front of every issue row, and the four counters in the top bar, saying what the issue wants from outside it: `needs you`, `running`, `done` or `queued`. Distinct from the **phase pill**, which says where a ticket stands inside its own run.
_Home_: `mmw-v2/board/page/board-logic.mjs`

**phase pill**:
The capsule on every ticket card saying where the ticket stands inside its own run — `queued`, `working`, `waiting`, `review`, `verify` or `landed` — computed from the ticket's fold and its event history. Distinct from the **phase** column of `status` and from the `stage` field of an event.
_Home_: `mmw-v2/board/page/board-logic.mjs`

**event display name**:
The English phrase an event row of the detail column shows for a pipeline **event** (Worker started, Ticket claimed, …), in place of the dotted identifier.
_Home_: `mmw-v2/board/page/board-logic.mjs`

**run line**:
The sentence under a ticket card's title naming what is or was running it: `host · model · effort` while a live session holds the ticket, `stopped · host · model` if a fault child stopped that session, `waiting for a slot · since HH:MM`, `claimed · no session yet`, `not dispatched`, or `closed, never dispatched`.
_Home_: `mmw-v2/board/page/board-logic.mjs`

**why**:
The reasons a ticket's lamp is orange, listed in the detail column's "Needs you" callout: one line per open `decision`, `fault` or `contract` child, one when the ticket was handed back with criteria abandoned, and one for a bounce not yet resolved.
_Home_: `mmw-v2/board/page/board-logic.mjs`

**event block**:
One stretch of consecutive events in a ticket's history sharing one phase, shown in the detail column collapsed to its most telling event and the time span it covers; only the newest block, and one whose events need attention, open by default.
_Home_: `mmw-v2/board/page/board-logic.mjs`

### The canvas

**container**:
A map or spec card on the canvas: it can expand, laying out its children — a map's decision tickets, or a spec's tickets — in a column to its right joined by an expand line. Distinct from a ticket or decision card, neither of which expands.
_Home_: `mmw-v2/board/page/canvas.mjs`

**canvas edge**:
One curve the canvas draws between two cards: a trunk line from a map to its spec column, an expand line from a container to a child in its first layer, or a block line between a blocked ticket (or decision) and its blocker. A block or expand line's state is `blocked` (the blocker is not yet cleared), `done` (cleared, but nothing behind it is running — the legend calls this state **walked**), or `flow` (cleared and being worked, drawn as a moving beam). Distinct from a **blocking edge**, the tracker relation a block line depicts.
_Home_: `mmw-v2/board/page/canvas.mjs`, `mmw-v2/board/page/board-logic.mjs`

**closeout bar**:
The stripe the canvas draws on a ticket card whose `closeout` field is set: the ticket was itself opened by a closing pass's `resolve-child`, out of a finding on the ticket its `closeout.from` names. Distinct from **closeout**, `ticket_state.py --closeout`.
_Home_: `mmw-v2/board/page/canvas.mjs`, `mmw-v2/board/board_data.py`

### Reading and refreshing

**read-state line**:
The line beside the top bar's counters naming when `tasks` was last read: quiet after an ordinary read, and hatched with the failed read's time and how long ago when GitHub could not be read and the page is showing the last good data instead.
_Home_: `mmw-v2/board/page/topbar.mjs`

**board polling**:
The background read of `GET /api/board` that `app.mjs` starts once immediately and repeats every 60 seconds while the page is visible, feeding the same repaint the top bar's manual refresh uses.
_Home_: `mmw-v2/board/page/board-feed.mjs`

**signature**:
The string `app.mjs` computes from what one column of the page reads, so that column is redrawn only when its signature changes rather than on every poll; a signature includes clock-derived text (a ticket's elapsed time), which is why that text keeps ticking.
_Home_: `mmw-v2/board/page/app.mjs`

### The settings sheet

**settings sheet**:
The dialog the top bar's gear opens, showing and editing this machine's `models.json`: one row per agent (host, model, effort) and the runner, validated and saved through `PUT /api/settings`. It writes nothing to GitHub.
_Home_: `mmw-v2/board/page/settings.mjs`

**host chip**:
One chip in the settings sheet's host row, one per host `hosts.json` names: solid when this machine's scan says the host answers, dashed for every other state (not installed, silent, Paseo not running, or not launchable on the selected runner).
_Home_: `mmw-v2/board/page/settings.mjs`, `mmw-v2/board/page/local-config.mjs`

**hatched**:
The board's mark, a diagonal fill, for a value that is not currently good, always paired with one line saying why: a settings cell whose saved value `start` would refuse, or the read-state line after a failed read.
_Home_: `mmw-v2/board/page/settings.mjs`, `mmw-v2/board/page/topbar.mjs`

**settings draft**:
The settings sheet's unsaved copy of the rows and runner being edited: compared against the last saved copy to show what changed, and against the scan to find what would be hatched. Discarded on cancel, close, or Esc.
_Home_: `mmw-v2/board/page/local-config.mjs`
