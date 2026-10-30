# Task board

The local task board over tracker state and machine-level model configuration. Its own terms describe presentation and freshness; ticket, map, spec, event and session retain the definitions of their owning contexts.

## Language

### The task board and what keeps it running

**task board**:
The local page served for a registered consuming repository, showing tracker state and editing this machine's saved agent configuration. It stores neither a second ticket state nor a second model configuration.

**`boards.json`**:
The machine-level registry at `MMW_HOME/boards.json` mapping each consuming repository's **main worktree** path to its task board's fixed local port. It holds no ticket or model state.

**`supervisor.py`**:
The task board process maintaining a server for each registered consuming repository. Its lifecycle is managed by the com.mmw.board LaunchAgent.

**page token**:
The secret `server.py` mints at every start and hands to the page, which sends it back as the `X-MMW-Token` header on every non-`GET` request. A write from another origin, a stale page or a bare `curl` is refused.

**`codeversion.py`**:
The task board code-version observer identifying a changed loaded implementation. It supports server and supervisor restart onto the installed version.

### What the page shows

**page regions**:
The task board's top bar, left issue list, canvas and detail column. The settings sheet is a dialog over these regions.

**Maps & specs**:
The task board's top-level issue grouping for maps and standalone specs with their children. It is distinct from a night, which is one execution of a spec's batch.

**lamp**:
The dot in front of every issue row, and the four counters in the top bar, saying what the issue wants from outside it: `needs you`, `running`, `done` or `queued`. Distinct from the **phase pill**, which says where a ticket stands inside its own run.

**phase pill**:
The capsule on every ticket card saying where the ticket stands inside its own run — `queued`, `working`, `review`, `verify` or `landed` — computed from the ticket's fold and its event history. Distinct from the **phase** column of `status` and from the `stage` field of an event.

**event display name**:
The English phrase an event row of the detail column shows for a pipeline **event** (Worker started, Ticket claimed, …), in place of the dotted identifier.

**run line**:
The ticket card's account of its current or past session, model and dispatch state. It is distinct from the card's phase pill and attention lamp.

**why**:
The reasons a ticket's lamp is orange, listed in the detail column's "Needs you" callout: one line per open `decision`, `fault` or `contract` child, one when the ticket was handed back with criteria abandoned, and one for a bounce not yet resolved.

**event block**:
One stretch of consecutive events in a ticket's history sharing one phase, shown in the detail column collapsed to its most telling event and the time span it covers; only the newest block, and one whose events need attention, open by default.

### The canvas

**container**:
A map or spec card on the canvas: it can expand, laying out its children — a map's decision tickets, or a spec's tickets — in a column to its right joined by an expand line. Distinct from a ticket or decision card, neither of which expands.

**canvas edge**:
A task board connection depicting parent expansion or blocking between issue cards. Its visual state describes whether the relationship is waiting, cleared or being worked, rather than creating a tracker dependency.

**closeout bar**:
The stripe the canvas draws on a ticket card whose `closeout` field is set: the ticket was itself opened by a closing pass's `route`, out of a finding on the ticket its `closeout.from` names. Distinct from **closeout**, `verify-ticket.py --closeout`.

### Reading and refreshing

**read-state line**:
The line beside the top bar's counters naming when `tasks` was last read: quiet after an ordinary read, and hatched with the failed read's time and how long ago when GitHub could not be read and the page is showing the last good data instead.

**board polling**:
The task board's periodic refresh of tracker-backed page data while visible. It is distinct from relay polling, which produces execution wakes.

**signature**:
The task board's comparison value for deciding whether displayed content needs repainting. It includes time-dependent content that the page shows.

### The settings sheet

**settings sheet**:
The dialog the top bar's gear opens, showing and editing this machine's `models.json`: one row per agent (host, model, effort) and the runner, validated and saved through `PUT /api/settings`. It writes nothing to GitHub.

**host chip**:
One chip in the settings sheet's host row, one per host `hosts.json` names: solid when this machine's scan says the host answers, dashed for every other state (not installed, silent, Paseo not running, or not launchable on the selected runner).

**hatched**:
The board's mark, a diagonal fill, for a value that is not currently good, always paired with one line saying why: a settings cell whose saved value `start` would refuse, or the read-state line after a failed read.

**settings draft**:
The settings sheet's unsaved edits, compared with saved configuration and current host availability. It is distinct from the persisted choices in models.json.
