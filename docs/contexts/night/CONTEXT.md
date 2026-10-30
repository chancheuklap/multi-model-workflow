# Night

Execution of an independent ticket or spec batch, including dispatch, landing, delivery and run feedback. Its sessions, watches and machine-local liveness records are distinct from the tracker records defined by Tickets and Ticket run.

## Language

### Roles

**agent**:
A session or subagent carrying an MMW assignment. Its concrete job is identified by the session role or subagent row rather than by a generic agent grade.

**session**:
A host process started by the user or a runner, with a continuing context and role. It is distinct from a subagent inside another session.

**orchestrator**:
The session controlling a spec batch or independent ticket through its watch, executor Playbook and delivery. It is distinct from the worker and has no dispatched-role model row.
_Avoid_: main agent, 编排者

**runner**:
The program managing dispatched sessions on this machine, reached through its runner adapter. The supported runner names are paseo, orca and herdr; a runner is distinct from the host it starts.

**runner adapter**:
The dispatch integration for one runner, translating shared session-management operations into that runner's commands. It is the runtime boundary used by dispatch, relay and watchdog.

**researcher**:
The briefed session role returning cited findings through the research skill. It is distinct from the investigation workflow that consumes those findings.

**candidate**:
The briefed session role producing one design in an arena comparison. It is distinct from an Eval participant whose comparison is blinded.

**retro-analyst**:
The briefed session role assessing one retrospective angle and returning its conclusion table. The orchestrator validates and records the returned assessments.

**review-axis, reader and default**:
The subagent-row family in roles.json for independent review axes, large-source reading and other named subagent work. Their host-specific model choices are separate from session-role rows.

### Places

**Paseo**:
One of the three runners, a daemon whose CLI is `paseo`. Its adapter starts each session in the directory it is given, never in a Paseo workspace.

**Paseo agent**:
A session Paseo runs, with an id, a title (`#<n> worker` or `#<n> reviewer`) and a status the Paseo adapter reads to answer `liveness`.

**workspace**:
The ticket-owned worktree and the sessions recorded for that ticket. Its cleanup does not imply deleting unlanded work preserved on a branch.

**wake**:
What the relay sends a session when an event it waits on lands on a ticket, `#<n> <event>`, or when every brief of a batch it started is done, `brief <batch> done`; either says only where to look. Distinct from a `watchdog:` line, which the watchdog sends itself and which is not acked.

**worktree**:
A git working tree used by an effort, ticket or merge within MMW's repository layout. The issue, fix, map and merge worktrees have distinct ownership and lifetimes.

**ticket branch**:
The branch `issue-<n>`, cut from `origin/<base branch>` by `start`, shared through `origin/issue-<n>` while the ticket is worked. Landing deletes both the local and origin copies when cleanup permits it.

**`issue-<n>`, `fix-<n>`, `map-<n>` and `merge-<slug>`**:
The MMW worktree-name family for ticket implementation, independent preparation, map efforts and serialized landing. The branch or run record identifies the particular owner of each worktree.

### Branches and integration

**base commit**:
The commit from which a ticket's work and independent review are compared, recorded with its worker start. It is distinct from the whole night's starting commit.

**night's base commit**:
The merge-base of a night's project and base branches, as `spec.opened` records them: where the night's landing and closing-pass commits start.

**base branch**:
The recorded integration target into which a ticket lands. In a night it is the batch's temporary integration branch, later accepted into the project branch.

**project branch**:
The consuming project's branch receiving an accepted effort or night. It is distinct from a ticket branch and a night's temporary integration base.
_Avoid_: 项目分支

**`MMW_BASE_REF`**:
The variable a repository's own commands receive as `origin/<base branch>` — every `CHECK:` shell and every run of the repository's `scripts/check` — so a check compares against the same base in any worktree or clone.

**`dispatch.sh integrate`**:
The worker's integration of its recorded base branch into the ticket branch before acceptance runs. A conflict remains available for resolution rather than rewriting ticket history.

**`dispatch.sh integrated`**:
The dispatch inventory of sibling tickets integrated since this worker started. The Spec review axis uses it to examine combined behavior.

**merge lock**:
The lock in the state directory naming which branch's merge worktree is in use, `merge-<slug>.lock`, so `open`, `advance`, `land`, `reverify` and `finish` take one merge at a time per branch.

### Dispatch

**landing pipeline**:
The MMW execution path from prepared implementation tickets through verified closeout and landing. It is narrower than the whole development workflow, which also includes discussion and preparation.

**`dispatch`**:
The [skill](../../../mmw-v4/skills/dispatch/SKILL.md) providing session dispatch, run control, model configuration and task board access. The executor Playbook decides when those capabilities act.

**`dispatch.sh`**:
The dispatch skill's script, whose verbs open, advance, land, suspend and finish a night and start, message, ask after and stop sessions through each runner's adapter.

**`dispatch.sh send`**:
A dispatch send that starts bounded, non-ticket assignments from brief files and collects their answers. It is distinct from the brief document defined in Ticket run.

**brief batch**:
The group of briefed sessions answering one sending session, with one batch identity and one completion wake. It is distinct from the implementation batch under a spec.

**`dispatch.sh board`**:
The command that makes sure the repository's task board is registered and answering and opens it, or prints its URL.

**`dispatch.sh pr`**:
The dispatch operation opening a delivery PR and reporting its checks and expected CI. Opening a PR owns the human review and acceptance of that delivery.

**start prompt**:
The assignment supplied when a host session starts, naming its governing file and particular input. Ticket sessions receive ticket identity and start evidence; briefed sessions receive their brief and report destination.

### Models and runners

**model-and-level pair**:
One selectable combination of a model and a reasoning effort that a host offers when it carries the reasoning effort inside the model rather than as a setting of its own; `models.py config set` selects among the pairs the scan returns.

**fast**:
A suffix in a model's own name, not a value of `effort`.

**thinking option**:
The value the Paseo runner passes as a host's thinking setting (`paseo run --thinking`): for most hosts the reasoning effort itself, one of the model's `thinkingOptionIds`. A host that offers thinking only as on or off takes `false` for `off` or no reasoning effort at all and `true` for every other reasoning effort, so it takes nothing else from the reasoning effort.

### The night's commands

**`dispatch.sh check`**:
The dispatch prerequisite check before a spec batch opens, covering the repository, installation and selected runtime configuration. It is distinct from running a tier of scripts/check.

**repository Space**:
The Nowledge Mem Space for one tracker repository, id `<owner>__<name>` in lower case, which `open` before the night opens and `start` before it starts a session each confirm, creating or repairing it when it is absent or wrong.

**`dispatch.sh open`**:
The dispatch operation beginning a spec watch and recording its integration and project branches. It is distinct from opening a preparation problem through to-tickets.

**`dispatch.sh finish`**:
The dispatch promotion of an accepted, closed night into its recorded project branch. It records spec.merged and closes the spec while preserving branch and worktree ownership.

**`dispatch.sh open-ticket`**:
The dispatch operation beginning a watch for one independent ticket rather than a spec batch.

**`dispatch.sh start`**:
The low-level dispatch operation starting a ticket worker or reviewer in its workspace and recording the session on the ticket.

**`dispatch.sh self`**:
The dispatch and runner-adapter identity query for the calling session.

**`dispatch.sh retract`**:
The dispatch recovery operation for a gone worker, preserving its work before releasing its claim and resources.

**`dispatch.sh wait`**:
The non-blocking dispatch read of a ticket session's newest result event after a wake. It is distinct from waiting for a session to finish.

**`dispatch.sh resume`**:
The dispatch message to an existing ticket worker carrying a correction or continuation. It reuses that worker session rather than silently replacing it.

**`dispatch.sh status`**:
The dispatch view of a spec batch's ticket state computed from the tracker, without asking runners for liveness.

**`dispatch.sh reverify`**:
The dispatch rerun of landed ticket criteria on the integration branch, recording regression or recovery. Its result is tied to the commit checked.

**`dispatch.sh findings`**:
The dispatch inventory of open finding children in a spec batch. It supplies the complete set the closing pass routes.

**`dispatch.sh summary`**:
The dispatch closeout of a finished night, recording repository-check evidence, finding routes and the NIGHT SUMMARY before closing its watch. It is distinct from the later accepted merge performed by finish.

**Memory closing**:
The night closeout's recorded decisions on shared experience for that spec. Its evidence limits distinguish a completed review from unavailable Memory access.

**`dispatch.sh memory-list`**:
The dispatch inventory of a spec's Memory records, with the decision-file skeleton used by Memory closing.

**`--memory-decisions` file**:
The Memory closing decision document identifying each reviewed Memory record, its decision, reason and supporting evidence.

**`retro`**:
The [skill](../../../mmw-v4/skills/retro/SKILL.md) supplying retrospective evidence gathering, recorded analyst assessments and owner-approved backlog decisions. The calling Playbook owns their order and scope.

**`status.py`**:
The dispatch skill's read-only script that computes where each of a spec's tickets stands from the tracker alone, for `status`, `advance`, `reverify`, `land` and `summary`. It keeps no state file.

**phase**:
The status view's display of a ticket's newest event. It is distinct from the task board's phase pill and an acceptance event's stage.

**holder**:
The session or unmatched claim currently holding a ticket according to tracker evidence. It is distinct from a lock holder and the blocker_hold of dependent work.

**in flight**:
Whether `land` may treat a ticket's work as still going on: open, and not handed back to `needs-triage`. Read off the tracker's state and labels alone, never off who holds the ticket.

**plan line**:
The machine-readable action family produced by status.py for dispatch execution, such as MERGE, RELEASE, DISPATCH and HOLD. It is distinct from a ticket fold's held state.

**`ARCHIVE`, archive**:
The workspace lifecycle action releasing that ticket's sessions, product resources and disposable worktree. Preserved unlanded commits remain on their branch; it is distinct from retiring a skill.

**worker-grades line**:
The status.py output family identifying a batch's tickets and their selected worker grades. Dispatch uses it for readiness and capacity checks.

**reverify result**:
The newest landed-result criterion run for a ticket, carrying the exact commit checked. It is distinct from the retrospective receipt required by the delivery flow.

**`dispatch.sh advance`**:
The dispatch batch executor step combining landing passed tickets, releasing completed holds and starting eligible work within capacity.

**`dispatch.sh land`**:
The dispatch landing and resource-closeout operation for independent tickets. It is distinct from a worker's ticket closeout, which records a pass before landing.

**`dispatch.sh suspend`**:
The dispatch operation stopping an open night safely when its pipeline cannot proceed, preserving pushed work and closing its watch for later recovery.

### The night

**night**:
One unattended execution of a spec's batch under an orchestrator, from its open watch through summary. Its name describes the run mode rather than the hour, and a one-ticket spec batch is still a night.

**closing pass**:
The night executor's routing of open finding children and completion of its shared-experience decisions after the frontier is exhausted. It is distinct from a ticket worker's closing steps.

**`dispatch.sh route`**:
The dispatch resolution of a ticket child as fixed, stale or implementation work, recorded on its original ticket.

### Liveness

**relay**:
The dispatch skill's `relay.py`, one process per repository, which reads the tickets its watches cover and turns each event a session waits on into a **wake** to that session. It decides nothing and writes nothing to the tracker.

**watch**:
The relay's association between tracked work and the session waiting for its results. It covers one spec, independent tickets or a brief batch without sharing a ticket between watches.

**wake queue**:
The relay's `queue.jsonl` in the state directory, one row per wake to send. Only an **ack** removes a row.

**recipient**:
The runner/session identity to which a wake is addressed. It is the ticket worker, its orchestrator or a brief batch's sending session, depending on the result.

**ack**:
The recipient's acknowledgment that it read the queued result. It removes the covered wake rows rather than recording implementation success.

**coalesced**:
The relay condition where an event shares an already queued, unacknowledged wake with the same ticket and event identity. It is distinct from the fold that computes a ticket's state.

**unconfirmed**:
A relay delivery whose send reached the session without confirming a new turn. It remains delivered until acknowledged rather than being treated as an unsent wake.

**good poll**:
A relay read-and-deliver cycle in which every required tracker read succeeded. It is distinct from a recorded cycle that encountered a read failure.

**cycle**:
One pass of the relay's read-and-deliver loop, recorded (`cycle_at`) whether or not its reads worked. The watchdog's `relay down` alert asks whether the relay has finished one within its **grace**.

**unattended stretch**:
Time with no **good poll** — the relay down, or its reads failing — measured less time spent delivering. The events of the stretch are delivered as ordinary wakes when the reads come back.

**grace**:
The configured bound for an unattended relay stretch and its health judgment. It is a liveness setting rather than an execution timeout.

**state directory**:
The machine-local directory for one repository's coordination records under MMW_HOME. Tracker events remain authoritative for ticket state.

**lock record**:
The coordination record identifying a lock holder and its purpose. Its process identity distinguishes a continuing holder from a reused process number.

**watchdog**:
The dispatch liveness process inspecting the relay and watched sessions and notifying the orchestrator of actionable problems. A confirmed stopped session produces its lost event rather than a guessed ticket result.

**liveness layer**:
The cooperating turn guard, relay-health check and runner-session check used to notice stopped coordination or work. It is distinct from a testing layer.

**alert**:
A watchdog notification about a coordination or session problem, sent directly as a watchdog line. It is distinct from a queued relay wake and a review finding.

**worktree activity**:
The most recent relevant commit or file activity in the worktree recorded for a session. It supplies evidence for distinguishing inactive work from a merely quiet ticket.

**idle session**:
A live runner session reported idle whose worktree has no recent activity and whose expected result is not pending. The watchdog records an alert rather than treating it as a completed task.

**stuck session**:
A session reported working without recent worktree or ticket progress under the watchdog's configured threshold. It is a liveness observation, not proof of a particular implementation fault.

**ticket waiting on its orchestrator**:
A watched ticket whose delivered result wake remains unacknowledged beyond the configured reminder threshold.

**`watchdog.py arm`**:
The watchdog operation establishing that one repository's watchdog is healthy without starting a second healthy instance.

**heartbeat**:
The relay or watchdog's recorded evidence of its own loop activity. It is distinct from proof that a ticket's product or worker succeeded.

**tolerance**:
The maximum heartbeat age used in the watchdog's own health judgment. It accounts for its polling interval rather than treating every slow round as death.

**turn guard**:
The dispatch skill's `turn-guard.py`, a hook on each host's turn-end event that arms the watchdog of every repository with an open watch. It never keeps a turn from ending.

### Retro

**registration**:
The issue recording a problem outside the acting session's current scope, with evidence, cost and the repository responsible for its fix. A lesson and a product problem have distinct kinds.

**occurrence**:
A lesson.seen record identifying one occurrence of a registered problem. Independent recurrence requires another ticket, spec or session rather than repeated comments on one occurrence.

**Retrospective**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/retrospective.md) for analyzing one run and recording checked analyst conclusions on registrations. Execution of those conclusions belongs to a separate owner-approved backlog review.

**`retro.py gather`**:
The retro operation collecting a run's registrations, signals and primary-source inventory for analysis by angle.

**evidence_checked**:
The retrospective inventory of primary sources actually opened. Missing access limits an assessment rather than proving that an event did not occur.

**earlier occurrence**:
An earlier lesson.seen supporting the same registered cause in an independent ticket, spec or session. It is recurrence evidence rather than a repeated comment in one case.

**stall event**:
A returned ticket, fault child or handoff result providing evidence of a stalled run. It is distinct from a normal blocking edge between planned tickets.

**proposal**:
The analyst conclusion propose recorded with its evidence and plan on a registration. It authorizes no implementation or issue disposition by itself.

**`retro.py apply`**:
The retro operation recording validated analyst conclusions and the retrospective receipt without carrying out those conclusions.

**`lesson.assessed`**:
The event preserving one retrospective assessment, its evidence, plan and qualification for proposal. It records judgment without changing the registration's disposition.

**backlog review batch**:
One owner-approved review of open lesson registrations grouped by root cause, with a recorded decision for each. It is distinct from a brief batch and a spec batch.

**`lessons.merged`**:
The event preserving an owner-approved backlog disposition and its batch identity. It marks the starting point for counting later assessments on that registration.

**retrospective receipt**:
The spec.retroed or ticket.retroed event accounting for recorded assessment rows and evidence limits, including unrecorded analysis or failed recording. It is distinct from an implementation result or approval of a proposal.

**`register-problem`**:
The [skill](../../../mmw-v4/skills/register-problem/SKILL.md) for registering an evidenced problem that cannot be fixed in the current work. It reuses the registration for repeated occurrences of the same cause.

**`correct`**:
The [skill](../../../mmw-v4/skills/correct/SKILL.md) for preparing an enforceable repair for a recurring agent mistake. Its mechanism and proof become implementation work under the owner's Go.

**Merging the lesson backlog**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/merging-the-lesson-backlog.md) grouping open registrations by root cause and applying the owner's decisions. Retrospective analysis alone is not approval for that action.

### Delivery

**the owner's page**:
The single visual reading and decision place for one pull request, published at the address or local path on the body's first line. Distinct from **the record**, which preserves the change's identification and evidence links.

**the record**:
The pull request body of fixed lines identifying the change and linking its ticket verdicts, landings, checks and unresolved work. The owner's explanation and decisions are on **the owner's page**.

**Opening a PR**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/opening-a-pr.md) settling one completed delivery through its page, record, checks, comments and owner-approved merge. Repairs remain in that delivery's existing scope and branch.

### Execution

**One ticket**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/one-ticket.md) orchestrating one owner-approved implementation ticket outside a spec, through worker proof, landing and its delivery PR. It is distinct from Work a ticket, the worker's assignment.

**Run a night**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/run-a-night.md) orchestrating a spec batch through unattended work, closing, delivery and the accepted merge. Its recorded watch supplies continuation and recovery for that run.

**Session pickup**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/session-pickup.md) reconstructing an unknown prior position from durable records and returning work to its current component. An already known step or active wake resumes directly.

**Pause safely**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/pause-safely.md) leaving a durable checkpoint on an explicit pause request. It is distinct from an unattended instruction to continue working.

**Worktree and simulator cleanup**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/worktree-cleanup.md) reclaiming confirmed unused worktrees and simulator resources while accounting for active work and uncommitted state.

**`resolving-merge-conflicts`**:
The [skill](../../../mmw-v4/skills/resolving-merge-conflicts/SKILL.md) for resolving merge or rebase conflicts and semantic interactions according to the changes' primary design evidence.
