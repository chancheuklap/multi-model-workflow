# Night

The main agent's commands that run a spec's published tickets, the runners that keep the sessions alive, the workspaces and branches they work in, and the three layers — relay, watchdog, turn guard — that deliver each result to whoever waits on it and notice a stopped session.

How to read an entry: the bold line is the term's name, and a term that is a literal string in a file, a command or a comment is named by that string exactly. The definition says in one or two sentences what the thing is and how it differs from its neighbours. `_Avoid_` lists wordings that name the concept less precisely in this repository's own text, each with the sense in which it is avoided. `_Home_` is the file that states the fact; an entry does not repeat what can be read there (a field list, an exit code, a command's switches, the branches of a behaviour), and when the two disagree, `_Home_` is right.

## Language

### Roles

**agent**:
Any session or subagent the pipeline starts or runs: the main agent, a worker, a reviewer, the advisor, a code-review axis. Four have a `models.json` row: `junior-worker`, `senior-worker`, `reviewer` and `advisor`.
_Home_: `mmw-v2/skills/dispatch/references/editing-models.md`

**session**:
A host process a runner started, or the main agent the user started; a session `dispatch.sh start` started is named on its ticket by its started event. A code-review axis runs inside the reviewer session and is not one.
_Home_: `mmw-v2/skills/dispatch/references/how-it-works.md`

**main agent**:
The session the user started, which runs one spec's night with the dispatch skill's commands, from `check` to `summary` and, after the user accepts the result, `finish`. It has no `models.json` row.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**runner**:
The program that starts and keeps running the sessions the pipeline starts on this machine — `paseo`, `orca` or `herdr` — reached only through its adapter, `scripts/runners/<runner>.sh` of the dispatch skill; `models.py runner` selects it. Distinct from the host, the agent program a session runs.
_Avoid_: host (for this; the host is the agent program the runner starts)
_Home_: `mmw-v2/skills/dispatch/scripts/runners/`

### Places

**Paseo**:
One of the three runners, a daemon whose CLI is `paseo`. Its adapter starts each session in the directory it is given, never in a Paseo workspace.
_Home_: `mmw-v2/skills/dispatch/scripts/runners/paseo.sh`

**Paseo agent**:
A session Paseo runs, with an id, a title (`#<n> worker` or `#<n> reviewer`) and a status the Paseo adapter reads to answer `liveness`.
_Home_: `mmw-v2/skills/dispatch/scripts/runners/paseo.sh`

**workspace**:
The per-ticket unit `dispatch.sh` opens and archives: the worktree `.worktrees/issue-<n>` together with every session the ticket's started events name. No runner creates or removes the worktree.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**wake**:
What the relay sends a session when an event it waits on lands on a ticket: `#<n> <event>`, which says only where to look. Distinct from a `watchdog:` line, which the watchdog sends itself and which is not acked.
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**worktree**:
A git worktree under the main checkout's `.worktrees/`: `issue-<n>` for one ticket's work, or a detached `merge-<slug>` for landing onto one branch, which persists and takes one merge at a time.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**ticket branch**:
The branch `issue-<n>`, cut from `origin/<base branch>` by `start`, shared through `origin/issue-<n>` while the ticket is worked, and deleted after it lands.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

### Branches and integration

**base commit**:
The merge-base of `origin/<base branch>` and the ticket branch: the commit a ticket's own work and its code review's diff start from. `start` records it as `base` in `worker.started` and `reviewer.started`; a later worker keeps the newest `worker.started` base until the ticket lands. Written `<base-commit>` as a placeholder. Distinct from the **night's base commit**.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**night's base commit**:
The merge-base of a night's project and base branches, as `spec.opened` records them: where the night's landing and closing-pass commits start. The `retro` skill reads it as `observed.base_commit`.
_Home_: `mmw-v2/skills/retro/SKILL.md`

**base branch**:
The temporary integration branch on `origin` a night's tickets merge into. `finish` merges it into the **project branch** once the user accepts the night.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**project branch**:
The branch a night's base branch was cut from and into which `finish` merges the accepted night, recorded in `spec.opened` as `project`.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`MMW_BASE_REF`**:
The variable a repository's own commands receive as `origin/<base branch>` — every `CHECK:` shell and every `.mmw/target.json` `checks` run — so a check compares against the same base in any worktree or clone.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`dispatch.sh integrate`**:
`dispatch.sh integrate <n>`: the worker's `--no-ff` merge of `origin/<base branch>` into its ticket branch before its criteria run. It never pushes or rebases; a conflict is left in the tree for the worker to resolve (exit 3), never aborted.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

### Dispatch

**landing pipeline**:
The path from a published spec to landed, closed tickets.
_Home_: `AGENTS.md`

**dispatch**:
Turning a ticket into a running session in its worktree with `dispatch.sh start <n> worker|reviewer`. A ticket or session that has been through it is dispatched.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`dispatch.sh`**:
The dispatch skill's script, whose verbs open, advance, land, suspend and finish a night and start, message, ask after and stop sessions through each runner's adapter. The skill's text calls it `<dispatch>`.
_Home_: `mmw-v2/skills/dispatch/SKILL.md`

**advise**:
`dispatch.sh advise <packet file>`: the one way the advisor is started, as a session of the selected runner in the current worktree. It writes no event.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`dispatch.sh board`**:
The command that makes sure the repository's task board is registered and answering and opens it, or prints its URL.
_Home_: `mmw-v2/skills/dispatch/references/task-board.md`

**start prompt**:
The text a session is given when started: which skill to use on which ticket, the standing sentences for working with nobody watching, and the Memory indexes or reviewer Rules for its role. An advisor's is `Use the advisor skill.` followed by the question packet.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

### The night's commands

**check**:
`dispatch.sh check <spec>`: the checks before a night opens — the branches, `install.sh --check`, the runner, the model rows and the worker-grade labels.
_Home_: `mmw-v2/skills/dispatch/references/how-it-works.md`

**repository Space**:
The Nowledge Mem Space for one tracker repository, id `<owner>__<name>` in lower case, which `open` creates or repairs and `start` verifies before it starts a session.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**open**:
`dispatch.sh open <spec>`: the night begins. It records the project branch, brings the base branch up to it, opens the relay's **watch** with the calling session as main agent, and posts `spec.opened`.
_Home_: `mmw-v2/skills/dispatch/references/how-it-works.md`

**`dispatch.sh finish`**:
`dispatch.sh finish <spec>`, run after the user accepts a closed night: it merges `origin/<base branch>` into the project branch, checks and pushes the result, posts `spec.merged`, and removes the base branch.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**open-ticket**:
`dispatch.sh open-ticket <n>`: what `open` is for one ticket outside a night, a relay watch on that ticket alone with the calling session as main agent.
_Home_: `mmw-v2/skills/dispatch/references/one-ticket.md`

**start**:
`dispatch.sh start <n> worker|reviewer`: has the selected runner start one agent on one ticket in its worktree, and posts the session's started event.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**adopt**:
`dispatch.sh adopt <n>`: makes the calling session ticket `<n>`'s worker when it picked the ticket up itself, writing the `worker.started` a `start` would have written.
_Home_: `mmw-v2/skills/dispatch/references/inside-a-ticket.md`

**self**:
The runner-adapter verb, and `dispatch.sh self`, answering which runner and session the calling process runs in.
_Home_: `mmw-v2/skills/dispatch/scripts/runners/`

**retract**:
`dispatch.sh retract <n>`: takes back what `start` left once the ticket's session is gone — commits and pushes its work, archives the workspace, gives back the slot and the claim — and posts `worker.retracted`.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**wait**:
`dispatch.sh wait <n> worker|reviewer`: reads that agent's newest result event once, after a wake has said it is there. It asks no runner and writes nothing.
_Home_: `mmw-v2/skills/dispatch/references/inside-a-ticket.md`

**resume**:
`dispatch.sh resume <n> "<text>"`: delivers the text to the worker still holding the ticket, through that worker's runner, and posts `worker.resumed`.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**status**:
`dispatch.sh status <spec>`: the table of the spec's tickets, computed from each ticket's fold without asking any runner.
_Home_: `mmw-v2/skills/dispatch/references/how-it-works.md`

**`dispatch.sh reverify`**:
`dispatch.sh reverify <spec>`: runs the criteria of every landed ticket of the spec again on the fetched base branch, reopening a red one for triage and closing a reopened one that is green again.
_Home_: `mmw-v2/skills/dispatch/references/how-it-works.md`

**summary**:
`dispatch.sh summary <spec> --memory-decisions <file>`: once nothing of the night is left running or unrouted, posts `spec.closed` with the `NIGHT SUMMARY` and closes the spec's watch.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**Memory closing**:
The part of the **closing pass** in which the main agent gives every Memory record labelled `mmw-spec-<spec>` one decision — `retain`, `propose`, `deprecate` or `supersede` — recorded as `memory_closing` in `spec.closed`.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**retro**:
The main agent's step right after `summary` records `spec.closed`: the retro skill, which writes the night's Retro Memory and posts the `spec.retroed` receipt.
_Home_: `mmw-v2/skills/retro/SKILL.md`

**`status.py`**:
The dispatch skill's read-only script that computes where each of a spec's tickets stands from the tracker alone, for `status`, `advance`, `reverify`, `land` and `summary`. It keeps no state file.
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**phase**:
The `phase` column of `status`: the name of the ticket's newest event, shown and never decided on. Distinct from the task board's **phase pill**.
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**`RELEASE`**:
The line `status.py --advance-plan` prints for a claim to be given back because an event has ended every hold on its ticket; `advance` then removes the assignee and posts `ticket.released`. It is not `lease.py release`.
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**advance**:
`dispatch.sh advance <spec>`: lands the batch's passed tickets on origin, gives back claims whose holds ended, then starts the frontier.
_Home_: `mmw-v2/skills/dispatch/references/how-it-works.md`

**land**:
`dispatch.sh land <n>`: the one-ticket form of **advance**, which lands the ticket's passed commit, releases its resources and closes its watch.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**suspend**:
`dispatch.sh suspend <spec>`: gives a night up when the fault is in the pipeline, stopping every session still holding a ticket, pushing their work, giving back every claim and slot, and closing the spec's watch. Distinct from `ABANDON:`, which gives up one criterion.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

### The night

**night**:
One run of a spec's published tickets under one main agent, from `open` to `summary`, at any hour.
_Home_: `mmw-v2/skills/dispatch/SKILL.md`

**closing pass**:
The pass the main agent runs when the frontier is empty: it routes every open `finding` child of the spec's tickets with **route**, runs `advance`, and repeats until none is left, then performs **Memory closing**.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**route**:
`dispatch.sh route <ticket> <child> …`: the one way a `finding` leaves the closing pass — fixed, stale, or made a ticket — recorded as `child.closed` on the ticket.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

### Liveness

**relay**:
The dispatch skill's `relay.py`, one process per repository, which reads the tickets its watches cover and turns each event a session waits on into a **wake** to that session. It decides nothing and writes nothing to the tracker.
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**watch**:
What the relay reads and whom it wakes about it: a night's spec, or tickets outside a night, with the session that opened it as its main agent. Two watches never share a ticket.
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**wake queue**:
The relay's `queue.jsonl` in the state directory, one row per wake to send. Only an **ack** removes a row.
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**recipient**:
The session a wake queue row is for, named by its (runner, session) pair: the ticket's worker for a reviewer's result or a freed slot, the main agent of the ticket's watch for a ticket's result or child.
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**ack**:
A recipient saying it has read a wake (`relay.py ack`, or `dispatch.sh ack <n> <event>`), which removes its rows up to that point.
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**state directory**:
`$MMW_HOME/state/<owner>__<name>/`, one per repository, holding every file the relay, the watchdog and the turn guard keep about that repository on this machine, and never a ticket's state.
_Home_: `mmw-v2/skills/dispatch/scripts/statedir.py`

**lock record**:
What a lock file in the state directory holds while its lock is taken — the holder's pid, process identity, start time and purpose — so a reader that will not take the lock can name the holder.
_Home_: `mmw-v2/skills/dispatch/scripts/statedir.py`

**watchdog**:
The dispatch skill's `watchdog.py`, one process per repository while a watch is open. It checks the relay and asks the runner of each silent held session whether it is alive, posting `worker.lost` or `reviewer.lost` for a stopped one and sending its other findings to the main agent as `watchdog:` lines.
_Home_: `mmw-v2/skills/dispatch/scripts/watchdog.py`

**heartbeat**:
`watchdog.json` in the state directory, which the watchdog rewrites every round. The watchdog is healthy when its lock names a live process that wrote a heartbeat within its **tolerance**.
_Home_: `mmw-v2/skills/dispatch/scripts/watchdog.py`

**tolerance**:
How old a watchdog heartbeat may be and still be fresh, and how long the tracker may go unread. For a runner, the tolerance of a `stopped` answer is how long a dead session may still read `alive`.
_Home_: `mmw-v2/skills/dispatch/scripts/watchdog.py`

**turn guard**:
The dispatch skill's `turn-guard.py`, a hook on each host's turn-end event that, in the main agent of an open watch, arms the watchdog and keeps the turn from ending while tickets are held and the watchdog is not healthy.
_Home_: `mmw-v2/skills/dispatch/scripts/turn-guard.py`
