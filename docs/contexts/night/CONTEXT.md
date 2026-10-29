# Night

The orchestrator's commands that run a spec's published tickets, the runners that keep the sessions alive, the workspaces and branches they work in, and the three layers — relay, watchdog, turn guard — that deliver each result to whoever waits on it and notice a stopped session.

## Language

### Roles

**agent**:
Any session or subagent the pipeline starts or runs: the orchestrator, a worker, a reviewer, a briefed session, a code-review axis. Every role `roles.json` marks as a session has a `models.json` row: `junior-worker`, `senior-worker`, `reviewer`, `advisor`, `researcher`, `explainer`, `synthesizer`.
_Home_: `mmw-v3/skills/dispatch/roles.json`, `mmw-v3/skills/dispatch/references/editing-models.md`

**session**:
A host process a runner started, or the orchestrator the user started; a session `dispatch.sh start` started is named on its ticket by its started event. A code-review axis runs inside the reviewer and is not one.
_Home_: `docs/contexts/night/how-it-works.md`

**orchestrator**:
The session the user started, which runs one spec's night with the dispatch skill's commands, from `check` to `summary` and, after the user accepts the result, `finish`. It has no `models.json` row.
_Avoid_: main agent, 编排者
_Home_: `mmw-v3/skills/mmw-mode/playbooks/run-a-night.md`

**runner**:
The program that starts and keeps running the sessions the pipeline starts on this machine — `paseo`, `orca` or `herdr` — reached only through its adapter, `scripts/runners/<runner>.sh` of the dispatch skill; `models.py runner` selects it. Distinct from the host, the agent program a session runs.
_Avoid_: host (for this; the host is the agent program the runner starts)
_Home_: `mmw-v3/skills/dispatch/scripts/runners/`

**runner adapter**:
The dispatch skill's `scripts/runners/<runner>.sh`, the one way `dispatch.sh`, the relay and the watchdog reach a **runner**: the verbs `start`, `send` and `liveness` (which answers `alive`, `stopped` or `unknown`), with `stop`, `self`, `attach` and the `catalog-*` reads, each answering with the same exit codes on every runner. Only the adapter runs a runner's own commands; every other script reaches the runner through it.
_Home_: `mmw-v3/skills/dispatch/scripts/runners/`

### Places

**Paseo**:
One of the three runners, a daemon whose CLI is `paseo`. Its adapter starts each session in the directory it is given, never in a Paseo workspace.
_Home_: `mmw-v3/skills/dispatch/scripts/runners/paseo.sh`

**Paseo agent**:
A session Paseo runs, with an id, a title (`#<n> worker` or `#<n> reviewer`) and a status the Paseo adapter reads to answer `liveness`.
_Home_: `mmw-v3/skills/dispatch/scripts/runners/paseo.sh`

**workspace**:
The per-ticket unit `dispatch.sh` opens and archives: the worktree `.worktrees/issue-<n>` together with every session the ticket's started events name. No runner creates or removes the worktree.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**wake**:
What the relay sends a session when an event it waits on lands on a ticket, `#<n> <event>`, or when every brief of a batch it started is done, `brief <batch> done`; either says only where to look. Distinct from a `watchdog:` line, which the watchdog sends itself and which is not acked.
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`

**worktree**:
A git worktree under the main worktree's `.worktrees/`: `issue-<n>` for one ticket's work; a merge worktree, the detached `merge-<slug>` for landing onto one branch (`<slug>` is the branch name with `/` replaced by `-`), which persists and takes one merge at a time; `fix-<n>` for a ticket a playbook opens outside a spec, where the daytime session commits its records and pushes `fix-<n>`; `map-<map number>` for a map's effort, created when Chart the map opens the map.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`, `mmw-v4/skills/mmw-mode/references/ticket.md` (`## Opening a ticket`), `mmw-v4/skills/mmw-mode/playbooks/chart-the-map.md` (`Create the map`)

**ticket branch**:
The branch `issue-<n>`, cut from `origin/<base branch>` by `start`, shared through `origin/issue-<n>` while the ticket is worked. Landing deletes both the local and origin copies when cleanup permits it.
_Home_: `mmw-v4/skills/dispatch/scripts/dispatch.sh`

### Branches and integration

**base commit**:
The merge-base of `origin/<base branch>` and the ticket branch: the commit a ticket's own work and its code review's diff start from. `start` records it as `base` in `worker.started` and `reviewer.started`; a later worker keeps the newest `worker.started` base until the ticket lands. Written `<base-commit>` as a placeholder. Distinct from the **night's base commit**.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**night's base commit**:
The merge-base of a night's project and base branches, as `spec.opened` records them: where the night's landing and closing-pass commits start.
_Home_: `mmw-v4/skills/dispatch/scripts/dispatch.sh`

**base branch**:
The branch on `origin` a ticket's work merges into: the newest `worker.started.into`, else the open night's `spec.opened.into`, else the branch of the checkout `start` runs from. In a night it is the temporary integration branch the night's tickets merge into, which `finish` merges into the **project branch** once the user accepts the night.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**project branch**:
The branch a night's base branch was cut from and into which `finish` merges the accepted night, recorded in `spec.opened` as `project`.
_Avoid_: 项目分支
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**`MMW_BASE_REF`**:
The variable a repository's own commands receive as `origin/<base branch>` — every `CHECK:` shell and every run of the repository's `scripts/check` — so a check compares against the same base in any worktree or clone.
_Home_: `mmw-v3/skills/verify-ticket/scripts/verify-ticket.py`

**`dispatch.sh integrate`**:
`dispatch.sh integrate <n>`: the worker's `--no-ff` merge of `origin/<base branch>` into its ticket branch before its criteria run. It never pushes or rebases; a conflict is left in the tree for the worker to resolve (exit 3), never aborted.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**`dispatch.sh integrated`**:
`dispatch.sh integrated <n>`: prints, one per line, every sibling ticket merged onto the base branch since this ticket's worker started, for the code-review skill's Spec axis to cross-check.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**merge lock**:
The lock in the state directory naming which branch's merge worktree is in use, `merge-<slug>.lock`, so `open`, `advance`, `land`, `reverify` and `finish` take one merge at a time per branch.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

### Dispatch

**landing pipeline**:
The path from a published spec to landed, closed tickets.
_Home_: `mmw-v4/README.md` `## Two ways a change reaches the product`

**dispatch**:
Turning a ticket into a running session in its worktree with `dispatch.sh start <n> worker|reviewer`. A ticket or session that has been through it is dispatched.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**`dispatch.sh`**:
The dispatch skill's script, whose verbs open, advance, land, suspend and finish a night and start, message, ask after and stop sessions through each runner's adapter.
_Home_: `mmw-v3/skills/dispatch/SKILL.md`

**brief**:
`dispatch.sh send <role> --follow "<file>" <brief file>...` for a role `roles.json` sends with a brief: starts one session per brief file in the sender's worktree, all answering the sending session. Each session writes only the files its brief names and makes no git write; it reports with `dispatch.sh report <batch>/<n> <file>`, and the answer is kept in the state directory. It writes no event.
_Home_: `mmw-v4/skills/dispatch/scripts/briefs.py`

**batch**:
What one `brief` call starts: its sessions, all of one role, all answering one parent session. The relay watches it as `briefs:<batch>` and wakes the parent once, `brief <batch> done`, when every brief has reported or been found lost; `dispatch.sh brief close <batch>` removes it. Distinct from a **backlog review batch** and from a spec's batch of tickets (`docs/contexts/tickets/CONTEXT.md`).
_Home_: `mmw-v4/skills/dispatch/scripts/briefs.py`

**`dispatch.sh board`**:
The command that makes sure the repository's task board is registered and answering and opens it, or prints its URL.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**`dispatch.sh pr`**:
The command that opens a ready pull request, reports whether GitHub CI runs for its base branch, and waits for checks.
_Home_: `mmw-v4/skills/dispatch/scripts/dispatch.sh` (`open_pr`)

**`dispatch.sh recheck`**:
The read-only check of affected landed criteria before a closing-pass push. Unlike `reverify`, it records no results on landed tickets and changes none of their states.
_Home_: `mmw-v4/skills/dispatch/scripts/dispatch.sh` (`recheck_spec`)

**start prompt**:
The text a session is given when started: to read the `mmw-mode` skill's `SKILL.md` in full first, the playbook it runs on its ticket, then its data: the worker's Memory indexes, the reviewer's base commit. A session `brief` starts is given its role's brief template and the brief file instead.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

### Models and runners

**model-and-level pair**:
One selectable combination of a model and a reasoning effort that a host offers when it carries the reasoning effort inside the model rather than as a setting of its own; `models.py config set` selects among the pairs the scan returns.
_Home_: `mmw-v3/skills/dispatch/references/editing-models.md`

**fast**:
A suffix in a model's own name, not a value of `effort`.
_Home_: `mmw-v3/skills/dispatch/references/editing-models.md`

**thinking option**:
The value the Paseo runner passes as a host's thinking setting (`paseo run --thinking`): for most hosts the reasoning effort itself, one of the model's `thinkingOptionIds`. A host that offers thinking only as on or off takes `false` for `off` or no reasoning effort at all and `true` for every other reasoning effort, so it takes nothing else from the reasoning effort.
_Home_: `mmw-v3/skills/dispatch/references/editing-models.md`, `mmw-v3/skills/dispatch/scripts/models.py` (`thinking_option`)

### The night's commands

**check**:
`dispatch.sh check <spec>`: the checks before a night opens — the branches, the session's `NMEM_SPACE`, `install.sh --check`, the runner, the model rows, the worker-grade labels, and one run of `scripts/check`'s default tier in the calling checkout.
_Home_: `docs/contexts/night/how-it-works.md`

**repository Space**:
The Nowledge Mem Space for one tracker repository, id `<owner>__<name>` in lower case, which `open` before the night opens and `start` before it starts a session each confirm, creating or repairing it when it is absent or wrong.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**open**:
`dispatch.sh open <spec>`: the night begins. It refuses a session whose `NMEM_SPACE` is not the repository's Space (ADR 0035), then records the project branch, brings the base branch up to it, opens the relay's **watch** with the calling session as orchestrator, and posts `spec.opened`.
_Home_: `docs/contexts/night/how-it-works.md`

**`dispatch.sh finish`**:
`dispatch.sh finish <spec>`, run after the user accepts a closed night: it merges `origin/<base branch>` into the project branch, runs `scripts/check`'s default tier on the result unless its tip is a ticket's landing merge, pushes it, posts `spec.merged`, closes the spec issue as completed, and removes the origin copy of the base branch when cleanup permits it. The local base branch and any worktree that has it checked out stay in place. The local project branch is created or fast-forwarded to the fetched origin tip, including in a clean worktree. A dirty worktree or local commits outside origin keep it unchanged, with the reason on stderr. A synchronization failure exits 2 and leaves the spec open for a retry.
_Home_: `mmw-v4/skills/mmw-mode/playbooks/run-a-night.md` (`#### 7. Merge the accepted night`)

**open-ticket**:
`dispatch.sh open-ticket <n>`: what `open` is for one ticket outside a night, a relay watch on that ticket alone with the calling session as orchestrator.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**start**:
`dispatch.sh start <n> worker|reviewer`: has the selected runner start one agent on one ticket in its worktree, and posts the session's started event.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**self**:
The runner-adapter verb, and `dispatch.sh self`, answering which runner and session the calling process runs in.
_Home_: `mmw-v3/skills/dispatch/scripts/runners/`

**retract**:
`dispatch.sh retract <n>`: takes back what `start` left once the ticket's session is gone — commits and pushes its work, archives the workspace, gives back the slot and the claim — and posts `worker.retracted`.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**wait**:
`dispatch.sh wait <n> worker|reviewer`: reads that agent's newest result event once, its newest `ticket.passed` or `ticket.returned` (worker) or `reviewer.reported` (reviewer), after a wake has said it is there. It does not block: with no result yet it exits 3 and tells the caller to end its turn. It asks no runner and writes nothing.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**`dispatch.sh resume`**:
`dispatch.sh resume <n> "<text>"`: delivers the text to the worker still holding the ticket, through that worker's runner, and posts `worker.resumed`.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**status**:
`dispatch.sh status <spec>`: the table of the spec's tickets, computed from each ticket's fold without asking any runner.
_Home_: `docs/contexts/night/how-it-works.md`

**`dispatch.sh reverify`**:
`dispatch.sh reverify <spec>`: runs the criteria of every landed ticket of the spec again on the fetched base branch, reopening a red one for triage and closing a reopened one that is green again.
_Home_: `docs/contexts/night/how-it-works.md`

**`dispatch.sh findings`**:
`dispatch.sh findings <spec>`: lists every open `finding` child of the batch, the exact set the closing pass must route, regardless of which one woke the orchestrator.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**summary**:
`dispatch.sh summary <spec> --memory-decisions <file>`, or `summary <spec> --memory-unavailable` while Nowledge Mem does not answer: once nothing of the night is left running or unrouted, posts `spec.closed` with the `NIGHT SUMMARY` and closes the spec's watch. It refuses, with nothing posted, while the batch holds a finding no `child.closed` accounts for, by the last count on its own `Findings routed:` line.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/run-a-night.md`

**Memory closing**:
The part of the **closing pass** in which the orchestrator gives every Memory record labelled `mmw-spec-<spec>` one decision — `retain`, `propose`, `deprecate` or `supersede` — recorded as `memory_closing` in `spec.closed`. While Nowledge Mem cannot list every record (it does not answer, or returns part of them), the night closes without it: `memory_closing` holds no decisions and the reason, and the records stay as they are (ADR 0035).
_Home_: `mmw-v3/skills/mmw-mode/playbooks/run-a-night.md` (step 7), `mmw-v3/skills/dispatch/scripts/dispatch.sh` (`memory_py`)

**memory-list**:
`dispatch.sh memory-list <spec>`: computes the repository Space id, pulls the spec's full `mmw-spec-<spec>` Memory record set, and prints a **`--memory-decisions` file** skeleton, one blank decision per active record. It exits 2 when Nowledge Mem does not answer or returns a truncated list.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**`--memory-decisions` file**:
The JSON file of **Memory closing** decisions, `{"decisions": [...]}`, that `summary` reads through `--memory-decisions`: `memory-list` prints its skeleton, and the orchestrator gives each record's entry a `decision`, `reason` and `evidence` (a URL for `propose`, and a `replacement_id` for `supersede`). `summary` refuses a file that leaves out an active record or gives one two decisions.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/run-a-night.md`

**retro**:
The capability that gathers evidence from a run and records the analyst's assessment of each row on its registration as `lesson.assessed`, recording `spec.retroed` or `ticket.retroed`; and, for a **backlog review batch**, lists the open registrations (`backlog`) and applies the owner's decisions (`merge-apply`).
_Home_: `mmw-v4/skills/retro/SKILL.md`

**`status.py`**:
The dispatch skill's read-only script that computes where each of a spec's tickets stands from the tracker alone, for `status`, `advance`, `reverify`, `land` and `summary`. It keeps no state file.
_Home_: `mmw-v3/skills/dispatch/scripts/status.py`

**phase**:
The `phase` column of `status`: the name of the ticket's newest event, shown and never decided on. Distinct from the task board's **phase pill**.
_Home_: `mmw-v3/skills/dispatch/scripts/status.py`

**holder**:
What `status.py` says holds a ticket: its newest live session (a worker or a reviewer), or a claim no session has taken over yet, or nothing. Distinct from ticket-run's **held**, the fold fact that a ticket stays off the frontier because some session or claim still holds it.
_Home_: `mmw-v3/skills/dispatch/scripts/status.py`

**in flight**:
Whether `land` may treat a ticket's work as still going on: open, and not handed back to `needs-triage`. Read off the tracker's state and labels alone, never off who holds the ticket.
_Home_: `mmw-v3/skills/dispatch/scripts/status.py`

**plan line**:
One line of `status.py`'s read-only plans, each read by `dispatch.sh` and nobody else: `MERGE`, `RELEASE` and `DISPATCH` from `--advance-plan`; `REVERIFY` and `RECOVER` from `--reverify-plan`; `MERGE`, `RELEASE`, `ARCHIVE`, `HOLD` and `NOTHING` from `--land-plan`. `RELEASE` gives back the tracker claim once an event has ended every hold on the ticket, and is not `lease.py release`; `HOLD <ticket> <why>` is this line, not the fold state ticket-run's **held** names.
_Home_: `mmw-v3/skills/dispatch/scripts/status.py`

**`ARCHIVE`, archive**:
Archiving a ticket's workspace: giving its product slot back, ending every session the ticket's events name, and deleting its worktree and the ticket's instance data, so nothing of the directory is kept. Unlanded ticket branches and their pushed commits remain; landing cleanup deletes contained ticket branches when no worktree has them checked out. `advance` archives a ticket's workspace once it lands, `land` once the ticket is closed (the `ARCHIVE` plan line), and `retract` a gone worker's; a ticket handed back keeps its workspace for the next `start`, and a workspace whose product is still up, or whose events cannot be read, is kept.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh` (`archive_workspace`), `mmw-v3/skills/dispatch/scripts/status.py`

**worker-grades line**:
One line of `status.py --worker-grades`: `BATCH <ticket>` for each child of the spec, `GRADE <ticket> [<label> ...]` for each one open and labelled `ready-for-agent`. `check` refuses the night when a `GRADE` line names a row `models.json` lacks, or a ticket carrying two; `suspend` reads the `BATCH` lines as the spec's children.
_Home_: `mmw-v3/skills/dispatch/scripts/status.py`

**reverify result**:
The newest `ticket.checked` with `run=reverify` on a landed or reopened ticket, carrying the commit it ran on. `summary` refuses the night unless every such ticket's newest one is green on the current tip of `origin/<base branch>` (`status.py --closeout-ready <spec> --at <commit>`), so a fix pushed after `reverify` needs `reverify` again. Distinct from `spec.retroed`, the event `finish` checks before merging.
_Home_: `mmw-v3/skills/dispatch/scripts/status.py`

**advance**:
`dispatch.sh advance <spec>`: lands the batch's passed tickets on origin, gives back claims whose holds ended, then starts the frontier, as many tickets as `max_workers` leaves room for.
_Home_: `mmw-v4/skills/dispatch/scripts/dispatch.sh` (`advance`), `mmw-v4/skills/dispatch/scripts/status.py` (`advance_plan`)

**land**:
`dispatch.sh land <n>`: the one-ticket form of **advance**, which lands the ticket's passed commit, releases its resources and closes its watch.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**suspend**:
`dispatch.sh suspend <spec>`: pauses a night when the fault is in the pipeline, stopping every session still holding a ticket, pushing their work, giving back every claim and slot, and closing the spec's watch. Its workspaces, branches and pushed commits stay, and `open` then `advance` take the same batch up again once the fault is fixed. Distinct from `ABANDON:`, which gives up one criterion.
_Home_: `mmw-v3/skills/dispatch/scripts/dispatch.sh`

### The night

**night**:
One run of a spec's published tickets under one orchestrator, from `open` to `summary`, at any hour, read the way a nightly build is: unattended while it runs, its result read cold the next morning.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/run-a-night.md`

**closing pass**:
The pass the orchestrator runs when the frontier is empty: it routes every open `finding` child of the spec's tickets with **route**, performs **Memory closing**, and runs `advance`, and repeats until no open finding is left.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/run-a-night.md`

**route**:
`dispatch.sh route <ticket> <child> …`: the one way a `finding` leaves the closing pass — fixed, stale, or made a ticket — recorded as `child.closed` on the ticket.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/run-a-night.md`

### Liveness

**relay**:
The dispatch skill's `relay.py`, one process per repository, which reads the tickets its watches cover and turns each event a session waits on into a **wake** to that session. It decides nothing and writes nothing to the tracker.
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`

**watch**:
What the relay reads and whom it wakes about it: a night's spec, or tickets outside a night, with the session that opened it as its orchestrator, or a brief **batch**, with the session that briefed it. Two watches never share a ticket.
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`

**wake queue**:
The relay's `queue.jsonl` in the state directory, one row per wake to send. Only an **ack** removes a row.
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`

**recipient**:
The session a wake queue row is for, named by its (runner, session) pair: the ticket's worker for a reviewer's result, the orchestrator of the ticket's watch for a ticket's result or child, the parent of a batch for its `brief <batch> done`.
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`

**ack**:
A recipient saying it has read a wake (`relay.py ack`, or `dispatch.sh ack <n> <event>`), which removes its rows up to that point.
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`

**coalesced**:
What the relay's log records when an event's translation is absorbed into an already-queued, unacked row rather than starting a new one, because the two wakes read `#<n> <event>` alike and a second row would only ask for a second ack of one reading of one ticket. Distinct from ticket-run's **fold**, a ticket's state replayed from its events.
_Avoid_: folded
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`

**unconfirmed**:
The flag the relay sets on a delivered row whose `send` answered 4: the text reached the session but no turn start was seen. It stays delivered and is sent again only when the relay restarts.
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`

**good poll**:
A **cycle** in which every read of the tracker succeeded, as against a cycle as such, which is recorded whether or not its reads worked. Only a good poll ends an **unattended stretch**.
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`

**cycle**:
One pass of the relay's read-and-deliver loop, recorded (`cycle_at`) whether or not its reads worked. The watchdog's `relay down` alert asks whether the relay has finished one within its **grace**.
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`

**unattended stretch**:
Time with no **good poll** — the relay down, or its reads failing — measured less time spent delivering. The watchdog's `not reading` **alert** fires once it exceeds **grace**; the events of the stretch are delivered as ordinary wakes when the reads come back.
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`

**grace**:
The `--grace` seconds parameter (default three intervals) bounding both an **unattended stretch** and the watchdog's own judgement of whether the relay is healthy.
_Home_: `mmw-v3/skills/dispatch/scripts/relay.py`, `mmw-v3/skills/dispatch/scripts/watchdog.py`

**state directory**:
`$MMW_HOME/state/<owner>__<name>/`, one per repository, holding every file the relay, the watchdog and the turn guard keep about that repository on this machine, and never a ticket's state.
_Home_: `mmw-v3/skills/dispatch/scripts/statedir.py`

**lock record**:
What a lock file in the state directory holds while its lock is taken — the lock holder's pid, its process identity (the process's own start time, so a pid later handed to another process is not mistaken for the same lock holder), when it took the lock, and its purpose — so a reader that will not take the lock can name the lock holder.
_Home_: `mmw-v3/skills/dispatch/scripts/statedir.py`

**watchdog**:
The dispatch skill's `watchdog.py`, one process per repository while a watch is open, running one round every `--poll` seconds (default 60). Each round it checks the relay, asks the runner of every session still holding a watched ticket and of every unreported brief what that session is doing (the **session table**), and reminds the orchestrator of every ticket waiting on it (the **ticket table**). It posts `worker.lost` or `reviewer.lost` for a stopped session and sends its other **alert**s to the orchestrator as `watchdog:` lines.
_Home_: `mmw-v4/skills/dispatch/scripts/watchdog.py`

**liveness layer**:
The three-part cover for a dead session that writes no event: the turn guard, re-arming the watchdog at an orchestrator's turn end, is the first layer; the watchdog's own check of the relay's **heartbeat** is the second; the watchdog asking each held session's runner whether it is alive and what it is doing is the third. A crash of the host an orchestrator runs in has no fourth layer, and is found by a person.
_Avoid_: layer (unqualified; tickets' **test layer** is a different concept sharing the word)
_Home_: `mmw-v4/skills/dispatch/scripts/watchdog.py`

**alert**:
One thing the watchdog's second or third layer notices — the relay down or not reading, the tracker unreadable, a ticket's events unreadable, a held ticket with no session to ask, a session whose liveness or turn state is unknown, a session showing a dialog, a **stuck session**, an **idle session**, or a **ticket waiting on its orchestrator** — sent to the orchestrator directly as a `watchdog:` line, never through the wake queue, and never acked.
_Avoid_: finding (this repository's other senses: a review finding, a ticket's `finding` child)
_Home_: `mmw-v4/skills/dispatch/scripts/watchdog.py`

**worktree activity**:
The latest commit time or file modification time in the worktree a session's start event or brief batch record names, never earlier than the session's start. What the watchdog reads to tell a session doing work from one doing nothing; a ticket's newest event is not consulted for an idle session.
_Home_: `mmw-v4/skills/dispatch/scripts/watchdog.py`

**idle session**:
A session whose runner answers `alive` and `idle` and whose **worktree activity** is at least `--idle` seconds old (default 3600), while no other session's result or landing on its ticket is pending. An **alert**, once per session and activity time.
_Home_: `mmw-v4/skills/dispatch/scripts/watchdog.py`

**stuck session**:
A session whose runner answers `working` and that has made no progress for `--stuck` seconds (default 7200), measured from the later of its **worktree activity** and its ticket's newest event, or a brief's send time. An **alert**, once per session and reference time.
_Home_: `mmw-v4/skills/dispatch/scripts/watchdog.py`

**ticket waiting on its orchestrator**:
A watched ticket with a `child.opened` that has no `child.closed` on it, or a delivered wake still in the **wake queue**. The watchdog alerts its watch's orchestrator at once and again every `--nudge` seconds (default 1800) until the children are routed and the wakes acked, whether or not a session holds the ticket.
_Home_: `mmw-v4/skills/dispatch/scripts/watchdog.py`

**arm**:
`watchdog.py arm --repo O/R [--wait S]`: makes the watchdog healthy. Does nothing when it already is; when a watchdog process holds its lock and is not healthy, starts nothing and says what fails; otherwise starts one and waits for it to be healthy. What `turn-guard.py` calls when the watchdog is not healthy.
_Home_: `mmw-v3/skills/dispatch/scripts/watchdog.py`

**heartbeat**:
A file in the state directory that a daemon rewrites to show it is alive: the watchdog's `watchdog.json`, written at start, after every ticket and at the end of every watchdog round, and the relay's `beat.json`, written every **cycle**. The watchdog is healthy when its lock names a live process that wrote its heartbeat within its **tolerance**.
_Home_: `mmw-v3/skills/dispatch/scripts/watchdog.py`

**tolerance**:
How old the watchdog's own heartbeat, and its last whole read of the tracker, may be and still count as fresh: `max(300, poll + margin)` seconds, so a slow poll interval does not read a healthy watchdog as dead.
_Home_: `mmw-v3/skills/dispatch/scripts/watchdog.py`

**turn guard**:
The dispatch skill's `turn-guard.py`, a hook on each host's turn-end event that, in the orchestrator of an open watch, arms the watchdog and keeps the turn from ending while tickets are held and the watchdog is not healthy.
_Home_: `mmw-v3/skills/dispatch/scripts/turn-guard.py`

### Retro

**登记**:
An issue recording a problem the acting session cannot fix in its current work, with evidence, cost, and a responsible repository. A lesson describes a way-of-working problem; a product problem stays in its own workflow.
_Home_: `mmw-v4/skills/register-problem/SKILL.md`

**出现**:
One `lesson.seen` on a registration, identifying where, when, and in which ticket, spec, or session the problem occurred. Repeated comments in one context do not satisfy the threshold for independent recurrence.
_Home_: `mmw-v4/skills/verify-ticket/scripts/events.py` (`lesson.seen`, `occurrences`)

**复盘**:
Sorting registered lessons and run signals by judgment, environment, and process, checking whether they still hold, and recording each assessment on its registration, where the owner's **backlog review batch** later acts on it. It reads events, issues, and git, not conversations or external memory.
_Home_: `mmw-v4/skills/retro/SKILL.md`

**gather**:
The retrospective's read-only command, selecting one spec or ticket and writing material for each nonempty angle plus `context.json`. Material includes current and related lessons, signals, reverted commits, orphaned children, recurrence after refusal, and approved closures without commits.
_Home_: `mmw-v4/skills/retro/scripts/retro.py` (`gather`)

**evidence_checked**:
Gather's inventory of opened primary sources. An unreadable source narrows the analysis; it does not prove that the thing it would have shown did not happen.
_Home_: `mmw-v4/skills/retro/scripts/retro.py` (`event_comments`, `inventory`)

**earlier occurrence**:
A registration's earlier `lesson.seen`, counted as independent recurrence when it belongs to another ticket, spec, or session. Its original evidence supports the same cause.
_Home_: `mmw-v4/skills/retro/scripts/retro.py` (`qualifies`)

**stall event**:
One of `ticket.returned`, `child.opened` with `kind=fault`, or `ticket.checked` with `result=handoff`. A registration arising from a stall has source `stall` and can qualify for a proposal on its first occurrence.
_Avoid_: blocking event
_Home_: `mmw-v4/skills/register-problem/SKILL.md`, `mmw-v4/skills/retro/scripts/retro.py`

**proposal**:
The analyst's conclusion `propose` on a registration, its plan recorded verbatim in a `lesson.assessed` row; `apply` asks the plan for no particular shape. Whether it qualifies (two independent occurrences, or one stall or owner's correction) is recorded beside it for reference; it changes nothing on the registration and authorizes no implementation.
_Home_: `mmw-v4/skills/retro/SKILL.md`, `mmw-v4/skills/retro/scripts/retro.py` (`qualifies`)

**apply**:
The retrospective's command that validates answer rows and evidence, records each accepted row as one `lesson.assessed` on the registration it names (a rerun of the same request records nothing twice), registers new signal-derived problems, and records the **retrospective receipt**. It closes, reopens, merges, relabels, edits or transfers no registration.
_Home_: `mmw-v4/skills/retro/scripts/retro.py` (`apply_answers`)

**`lesson.assessed`**:
The event `apply` writes on a registration for one accepted answer row: the conclusion as the analyst wrote it (`merge:<target>`, `reject`, `candidate` or `propose`), its reason, evidence and plan, the run it came from, whether it qualifies, and the request that wrote it. A record of judgement, never an action on the registration.
_Home_: `mmw-v4/skills/verify-ticket/scripts/events.py`, `mmw-v4/skills/retro/scripts/retro.py` (`apply`)

**backlog review batch**:
One owner-approved review of the open problem registrations, run by `playbooks/merging-the-lesson-backlog.md`: the owner decides each root-cause group on one page, and `retro.py merge-apply` carries out the closures, merges and keeps under one batch identifier. Distinct from a brief **batch** and from a spec's batch of tickets.
_Home_: `mmw-v4/skills/mmw-mode/playbooks/merging-the-lesson-backlog.md`

**`lessons.merged`**:
The event recording the owner's decision on one registration in a **backlog review batch**: `closed`, `kept`, `merged:<owner/repo#n>`, `spec:<n>` or `ticket:<n>`, with the batch identifier. Assessments counted toward the registration's next review start after it.
_Home_: `mmw-v4/skills/verify-ticket/scripts/events.py`, `mmw-v4/skills/retro/scripts/retro.py` (`merge-apply`)

**retrospective receipt**:
The `spec.retroed` or `ticket.retroed` event recording how many rows were recorded under each conclusion, recurrence after refusal, landed proposals, and evidence completeness. Its `problems` list records each row's registration and conclusion; a row whose code names no registration is listed there with conclusion `unrecorded`, its code as written and the reason, while the receipt itself stays `result=recorded`. A receipt with `result=unrecorded` means the whole retrospective failed to record and carries only its reason.
_Home_: `mmw-v4/skills/verify-ticket/scripts/events.py`
