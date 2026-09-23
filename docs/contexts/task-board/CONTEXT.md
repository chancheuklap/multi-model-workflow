# Task board

The local browser page over the pipeline's work: one small HTTP server per registered consuming repository, reading that repository's ticket state from the tracker and reading or writing this machine's agent configuration. The command that opens it, `dispatch.sh board`, is defined in `docs/contexts/night/CONTEXT.md`. Everything else the page shows is named by the term the other five contexts give it, in English, except an event row of the detail column, which shows an **event name**.

How to read an entry: the bold line is the term's name, and a term that is a literal string in a file, a command or a comment is named by that string exactly. The definition says in one or two sentences what the thing is and how it differs from its neighbours. `_Avoid_` lists wordings that name the concept less precisely in this repository's own text, each with the sense in which it is avoided. `_Home_` is the file that states the fact; an entry does not repeat what can be read there (a field list, an exit code, a command's switches, the branches of a behaviour), and when the two disagree, `_Home_` is right.

## Language

### The task board and what keeps it running

**task board**:
The local browser page for reading a spec's ticket state and editing this machine's `models.json`, served on `127.0.0.1` by one `server.py` per registered consuming repository. A model change goes through the same validation and write as `models.py config`.
_Home_: `mmw-v2/board/server.py`

**`boards.json`**:
The machine-level registry at `MMW_HOME/boards.json` mapping each consuming repository's main-checkout path to its task board's fixed local port. It holds no ticket or model state.
_Home_: `mmw-v2/board/supervisor.py`

**`supervisor.py`**:
`mmw-v2/board/supervisor.py`, the process the `com.mmw.board` LaunchAgent keeps alive, which starts and restarts `server.py` for every repository `boards.json` registers.
_Home_: `mmw-v2/board/supervisor.py`

**page token**:
The secret `server.py` mints at every start and hands to the page, which sends it back as the `X-MMW-Token` header on every non-`GET` request. A write from another origin, a stale page or a bare `curl` is refused.
_Home_: `mmw-v2/board/server.py`

### What the page shows

**The Night**:
What the task board calls one row of its left column and the tree it opens on the canvas: one top-level map, or a spec no open map holds, with every spec and ticket under it. Distinct from a **night**, one run of one spec's tickets.
_Home_: `mmw-v2/board/page/tasks.mjs`

**lamp**:
The dot in front of every issue row, and the four counters in the top bar, saying what the issue wants from outside it: `needs you`, `running`, `done` or `queued`. Distinct from the **phase pill**, which says where a ticket stands inside its own run.
_Home_: `mmw-v2/board/page/board-logic.mjs`

**phase pill**:
The capsule on every ticket card saying where the ticket stands inside its own run — `queued`, `working`, `waiting`, `review`, `verify` or `landed` — computed from the fold. Distinct from the **phase** column of `status` and from the `stage` field of an event.
_Home_: `mmw-v2/board/page/board-logic.mjs`

**event name**:
The English phrase an event row of the detail column shows for a pipeline **event** (Worker started, Ticket claimed, …), in place of the dotted identifier.
_Home_: `mmw-v2/board/page/board-logic.mjs`
