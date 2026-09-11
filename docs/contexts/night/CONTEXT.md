# Night

The night is the half of the landing pipeline that runs while nobody watches: dispatching sessions onto tickets, the runners that keep those sessions alive, the workspaces and branches they work in, and the three layers — relay, watchdog, turn guard — that make sure a result reaches whoever waits on it and that a dead session is noticed. This file fixes the name of everything that half invents, so that a session starting with an empty context uses the same word the last one used.

How to read an entry: the bold line is the term's only name; a term whose name is a literal string that appears in a file, a command, or a comment is named by that string exactly (case, colon, and all). The definition says what the thing is and what sets it apart from its neighbours. `_Admitted_` lists the one other wording that may appear in prose. `_Avoid_` lists dead words: a sentence in this repository that uses one is wrong; an item followed by a note in parentheses says in which sense the word is dead. `_Home_` is the file whose text or code the definition is taken from; when this file and that one disagree, that one is right and this file is rewritten. An attribute that can be had by reading that file — a field list, an exit code, a command's switches, the branches of a behaviour — is not repeated here: an entry says what the term is and how it differs from its neighbours, and points at `_Home_` for the rest.

## Language

### Roles

**agent**:
Any session or subagent this pipeline sends out or runs: the main agent, a worker, a reviewer, the verifier, the advisor, a code-review axis subagent. The five that have a row of their own in `models.json` are `junior-worker`, `senior-worker`, `reviewer`, `verifier` and `advisor`.
_Avoid_: board
_Home_: `~/.mmw/models.json`

**session**:
A host process a runner started, or the main agent the user started themselves. It carries a host. A session `dispatch.sh start` started is named on its ticket by its started event — `worker.started`, `reviewer.started` or `verifier.started` — whose payload carries the runner that runs it and that runner's own id for it, always as a pair, together with the machine it was started on. The main agent, a worker, a reviewer, the verifier, and the advisor are sessions; the three code-review axis subagents are not — they are subagents inside the reviewer session.
_Avoid_: 会话 (as a term), pane, terminal (for this)
_Home_: `~/.mmw/models.json`

**main agent**:
The session the user started themselves. By day it works with the user to produce specs and tickets; by night it runs `check`, then `open`, then `advance`, then on each **wake** `status`, one `advance` and `ack`, the **收口轮** when the frontier is empty and open `finding` children remain, then `reverify` and `summary`, and after the user accepts the result `finish`; it only reads tickets. It is the one agent with no row in `models.json`; it is tied to no host. One main agent holds one spec.
_Avoid_: coordinator, orchestrator, 编排者, 主 agent, 出票的主 agent, 落地 agent, the single Claude Code session, mmw-main, board
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**runner**:
The program that runs the sessions this pipeline starts on this machine: `paseo`, `orca` or `herdr`, one adapter each, `scripts/runners/<runner>.sh` of the dispatch skill. Every runner operation, including optional worktree association, task-board opening and catalog access, crosses that adapter. Its `# MMW_USES:` lines are the authoritative declaration of every runner command it calls, and `install.sh --check` compares them with the binary. The runner is not the host: the host is the agent program a session runs, while the runner keeps the session running and reachable. `dispatch.sh` creates and removes worktrees with git. Tonight's runner is selected by `python3 models.py runner`: `MMW_RUNNER`, then the saved `runner`; only a saved `auto` permits detection from the current process, and detection names only a runner this skill has an adapter for and that does not cut its own worktree, followed by `orca`. Saved rows are resolved against the selected runner's catalog. Once a session is started, every later command asks the runner named by its started event, and no other.
_Avoid_: backend, night-process host, 夜间进程宿主, host (for this)
_Home_: `mmw-v2/skills/dispatch/scripts/runners/`

### Places

**Paseo**:
One of the three runners, a daemon whose sessions are Paseo agents; its CLI is `paseo`. Its adapter starts each session in one call, in the directory it is given, never in a Paseo workspace (`PASEO_WORKSPACE_ID` is stripped, because `paseo run` ranks it above `--cwd`). A `models.json` row selected for Paseo is resolved against Paseo's provider catalog. Catalog, status, and diagnostic commands cross the Paseo adapter as its own three extra verbs, whose `MMW_USES` declarations let `install.sh --check` detect command changes.
_Avoid_: terminal multiplexer
_Home_: `mmw-v2/skills/dispatch/scripts/runners/paseo.sh`

**Paseo agent**:
A session Paseo runs. It has an id (the `session` of a started event whose `runner` is `paseo`, when `start` started it), a title (`#<n> worker`, `#<n> reviewer`, or `#<n> verifier`), a cwd whose basename is the worktree slug, and a `status`, which the Paseo adapter reads to answer `liveness`.
_Home_: `mmw-v2/skills/dispatch/scripts/runners/paseo.sh`

**Paseo subagent**:
A Paseo agent started from inside another Paseo agent, which Paseo records as its parent. A reviewer or verifier the worker starts is one only when both run on Paseo. Nothing in the pipeline relies on the parent link, and no verb of the Paseo adapter reads it: a result wakes the session its **recipient** rule names, whichever runner either runs on, and landing stops every session the ticket's started events name, one by one.
_Home_: `mmw-v2/skills/dispatch/scripts/runners/paseo.sh`

**workspace**:
The per-ticket unit `dispatch.sh` opens and archives: the worktree `<main checkout>/.worktrees/issue-<n>` together with every session the ticket's started events name. `start` opens it with git, has tonight's runner start a session in it by absolute path, writes that path into the started event, and asks the runner adapter to associate the ticket with the worktree where that capability exists. That association neither creates nor owns the worktree, and failure does not stop the session. Archiving it — `advance` after merging that ticket's branch, `land`, `retract` — gives back the product slot its worktree holds, if it holds one, stops each of those sessions through the runner its event names, removes the worktree with git, and removes its instance data. A `ticket.bounced` stops the ticket's sessions at once, and the next `advance` stops the sessions of a `ticket.returned`; both leave the worktree and its instance data standing for triage. No runner creates or removes a worktree.
_Avoid_: 工作区 (for the git sense, that is a worktree), pane, monitor tab, Herdr workspace, Paseo workspace
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**Agent profile**:
A hand-written entry in `~/.paseo/config.json` under `daemon.agentProfiles`. It is not MMW config: `install.sh` does not generate one from `models.json`. Notes containing `from models.md` identify leftover generated profiles from the retired Markdown format; `--check` reports `残留` and install drops them. Hand-written profiles are left alone.
_Home_: `mmw-v2/install.sh`

**finish notification**:
The message a runner delivers to the session that started an agent through that runner's own tools, saying the agent finished, errored, was closed, or needs permission. `start` starts every session through the runner adapter, never through those tools, so nothing in the pipeline waits on one: a result is an event on the ticket, and the **relay** turns it into a **wake**. No live script in this repository reads one.
_Avoid_: wakeup loop, re-prompt, STOPPED, TIME LIMIT, `mmw board:` line, pane event, turn, turn.py, board log
_Home_: `docs/adr/0020-wakes-come-from-the-board.md`

**wake**:
What the **relay** sends a **recipient** when an event it waits on lands on a ticket: `#<n> <event>`, the ticket number and the event's name and nothing else, through the `send` of the runner that runs the recipient (`relay.recovered since <time>` for the one row about the relay itself). A worker is woken for `reviewer.reported`, `verifier.passed` and `verifier.failed`, for `reviewer.lost` and `verifier.lost`, and with `worker.queued` when its ticket waits for a product slot and one is given back; the main agent of the ticket's watch for `ticket.passed`, `ticket.returned`, `ticket.refused`, `child.opened` of kind `fault` or `decision`, `worker.lost` and `relay.recovered`. What happened is read on the ticket; the wake only says where to look. It can cut short a command the recipient was running, so that command is run again first; then the recipient reads the event, acts, and acks the wake. No script sends one: `verify-ticket.py` posts events and tells nobody, and no runner's own notification is relied on. A `watchdog:` line is not a wake: the **watchdog** sends it itself, and it is not acked.
_Admitted_: wake-up
_Avoid_: ticket message, closeout notification, 通知 (as a term)
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**worktree**:
Either the per-ticket git worktree of a workspace, `<main checkout>/.worktrees/issue-<n>` on the ticket branch, or a detached merge worktree: `<main checkout>/.worktrees/merge-<slug>` for `advance`, `land` and `reverify`, and the same under the project branch's slug while `finish` merges a base branch back. The slug is the branch name with every `/` replaced by `-`, which is why a slug cannot be read back as a branch name. A merge worktree is reset to its authoritative origin branch before use and persists so ignored dependencies and caches survive. After `advance`, `land` or `finish`, a merge worktree whose corresponding origin branch no longer exists is removed together with its lock when that lock can be acquired; a held lock preserves both. After the accepted base branch is contained in the project branch, `finish` removes the base branch's merge worktree and lock. One lock per merge target — `merge-<slug>.lock` in the state directory — permits one merge at a time. A runner receives only the ticket worktree.
_Avoid_: 工作区, checkout (when this is meant), ~/.mmw/worktrees
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**ticket branch**:
The branch `issue-<n>`, shared through `origin/issue-<n>` while a ticket is worked and deleted locally and on origin after it lands. `start` cuts a new one from `origin/<base branch>` and pushes it with its upstream set before the session runs; no path rebases, squashes or force-pushes it.
_Admitted_: `issue-<n>`
_Avoid_: branch (bare), 分支名 (as a term)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

### Branches and integration

**base commit**:
The commit supplied to code review. `start <n> reviewer` computes it as the merge-base of `origin/<base branch>` and the ticket branch, falls back to the newest `worker.started.base` when they share none, records it in `reviewer.started`, and uses it for `git diff <base-commit>...HEAD`. A replacement worker keeps the first `worker.started.base`. The first `worker.started.base` and the base commit bound the first-parent commits the Spec axis reads. Written `<base-commit>` as a placeholder.
_Avoid_: base-commit (in prose), 起点 commit, cut point, 切点, review boundary, remote base, base tip, integrated tip
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**base branch**:
The temporary integration branch on `origin` a night's tickets merge into; `origin/<base branch>` is authoritative and a local branch of the same name is a cache. The main agent opens the night on it, `spec.opened` and `worker.started` name it in `into`, and after user acceptance `finish` merges it into the recorded project branch and removes every contained clean copy of it.
_Avoid_: main branch, 基线分支, main (as a name)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**project branch**:
The branch from which a night's base branch was cut and to which `finish` returns the accepted night. `open` records it in `spec.opened.project`, preferring an earlier such event, then the base branch's creation reflog, `branch.<base branch>.vscode-merge-base`, and finally the uniquely closest eligible origin branch; a tie or no candidate is a refusal that prints the `git config branch.<base branch>.vscode-merge-base <project branch>` to run. It is pushed before the night opens and is never merged into the repository default branch by MMW.
_Avoid_: default branch (for this), target branch, parent branch
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`MMW_BASE_REF`**:
The environment variable a repository's own commands receive as `origin/<base branch>` — every `CHECK:` shell `verify-ticket.py` runs through gate-check, and the `.mmw/target.json` `checks` it runs at closeout, at a landing merge and at `reverify`. The branch is the newest `worker.started.into`; `finish` supplies `origin/<project branch>` instead, because that is what its merge is checked against. It makes a check's comparison base portable across ticket worktrees, detached merge worktrees and fresh clones instead of naming a machine-local branch.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`dispatch.sh integrate`**:
`dispatch.sh integrate <n>`, run by the worker from its own worktree on `issue-<n>` before its criteria, brings `origin/<base branch>` — the newest `worker.started.into` — into the ticket branch with a `--no-ff` merge, and names the tickets it brought in (the `Merge branch 'issue-<n>'` first-parent subjects in the range). It never pushes, rebases or aborts.
_Avoid_: integrate (bare), update the branch, sync (as a term), pull
_Home_: `mmw-v2/skills/dispatch/references/inside-a-ticket.md`

**conflict report**:
The stderr account printed when `integrate` leaves `MERGE_HEAD` in the ticket worktree: the incoming tickets by number and title, the conflicted files, and the way out. Landing conflicts do not produce one: they are aborted in the detached merge worktree and recorded as `ticket.bounced` with the conflicted files.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

### Dispatch

**landing pipeline**:
The whole path from spec to closed ticket, made of stations that each have an entry here: by night **dispatch**, **preflight**, the worker's closing steps, **closeout**, **land**, **advance** and the **收口轮**; in the morning **reverify**, **NIGHT SUMMARY** and the triage queue. What feeds the night — **publish**, a spec, its tickets, their lint — is the day's work and has its own entries. Every rule of the path lives with its station; this entry only names them.
_Admitted_: ticket pipeline (in triage text)
_Avoid_: 流水线, this pipeline (as a name), 落地流水线
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**dispatch**:
Turning a ticket into a running session in its worktree: `dispatch.sh start <n> worker|reviewer|verifier`. The script checks the ticket may start, reads the role's `models.json` row, opens the workspace, computes the started event's base commit from `origin/<base branch>` and the ticket branch, has tonight's runner start the session, writes its started event (`worker.started`, `reviewer.started` or `verifier.started`) on the ticket, and prints the session id. The caller gives the ticket number and the kind; the worker-grade label picks which worker row. A ticket or session that has been through it is **dispatched**.
_Avoid_: 派发 (as a term), run (as a dispatch.sh verb)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`dispatch.sh`**:
The dispatch skill's script: `board`, `check <spec>`, `open <spec>`, `open-ticket <n>`, `adopt <n> [--into <branch>]`, `self`, `advance <spec>`, `integrate <n>`, `land <n>`, `start <n> worker|reviewer|verifier`, `retract <n>`, `wait <n> worker|reviewer|verifier`, `ack <n> <event>` / `ack relay.recovered`, `resume <n> "<text>"`, `status <spec>`, `reverify <spec>`, `summary <spec>`, `finish <spec>`, `suspend <spec>`, `route <ticket> <child> fixed|stale|became-ticket [<new ticket>]`. `--tools <directory>` may appear anywhere and any number of times, and is searched before the resolved location of another skill's script. It starts, messages, asks after and stops a session only through the adapter of the runner that runs it; the ticket's events carry its shared state. It reads the worker-grade label and nothing else to pick the worker row. The skill's own text calls it `<dispatch>`.
_Home_: `mmw-v2/skills/dispatch/SKILL.md`

**`dispatch.sh board`**:
The task board entry command, run from any checkout or worktree: it makes sure the consuming repository's task board is registered in `boards.json` and answering, then has tonight's runner's `open-url` open it in the current worktree, or prints its URL when that adapter does not implement `open-url`.
_Home_: `mmw-v2/skills/dispatch/SKILL.md`

**dispatch line**:
The sentences a session is given when started — which skill to use, on which ticket, and the standing sentences that say nobody is watching. A worker gets `Use the implement skill to work ticket #<n>.` plus the autonomous sentence, the product-rules sentence and the pipeline-fault sentence; a reviewer gets `Use the code-review skill to review ticket #<n> from base commit <base-commit>.` plus the autonomous sentence; a verifier gets `Use the verdict skill to verify ticket #<n>.` plus the autonomous and product-rules sentences. The three standing sentences are the `AUTONOMOUS`, `PRODUCT_RULES` and `PIPELINE_FAULT` constants of `dispatch.sh`, the first of them `You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work.` The runner is handed the session's title beside the line — `#<n> worker`, `#<n> reviewer` or `#<n> verifier` — so the sessions sharing one worktree can be told apart. A live worker gets `resume` instead.
_Avoid_: 派发 (as a term)词, prompt (bare)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

### The night's commands

**check**:
`dispatch.sh check <spec>`: infers the current base branch's project branch, fetches origin, reports each branch's pending push count and verifies the push by dry-run without changing origin; runs `install.sh --check`; confirms tonight's runner has an adapter; resolves the `models.json` row of each worker grade, the reviewer and the verifier against that runner's catalog; when Paseo is tonight's runner, refreshes each distinct host's snapshot with the Paseo adapter's `diagnostic` and then confirms that host reads `available` in the adapter's `catalog-status` (printing the diagnostic sentence under a refusal); and confirms every queued ticket has at most one worker-grade label that `models.json` contains. Exit 0 all passed; exit 2 one or more failed, stderr one `dispatch: …` line per failure. Do not `open` on 2.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**open**:
`dispatch.sh open <spec>`: the night begins. It infers the project branch from an earlier `spec.opened.project`, the base branch's creation reflog, `branch.<base branch>.vscode-merge-base`, or the uniquely closest eligible origin history, in that order. Before opening it rejects a default base or project branch and any local/origin divergence, then fast-forward pushes local-only or locally ahead project and base branches. The relay opens a **watch** on the spec with the calling session as its main agent, named by the runner and session its adapter's `self` reads (`relay.py start --repo <owner/name> --spec <spec> --runner <runner> --session <session>`), starting the relay when none runs, and `spec.opened` is written on the spec naming that runner, session, `into` and `project`. Opening the same night again keeps that project branch, makes the calling session its main agent and touches no other watch. `advance` refuses a night that is not open, and `summary` and `suspend` close its watch. Exit 0 opened; exit 2 refused, the reason on stderr.
_Avoid_: register (as the name of this), 开夜 (as a term)
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**`dispatch.sh finish`**:
`dispatch.sh finish <spec>`, run by the main agent after the user accepts a closed night, merges `origin/<base branch>` into the recorded project branch in a detached merge worktree, runs repository checks with `MMW_BASE_REF=origin/<project branch>`, fast-forward pushes the checked result, and writes `spec.merged`. It then removes the contained base branch from origin and locally, clean worktrees that have it checked out, the merge worktree and its lock. It refuses before changing anything while the spec carries no `spec.closed`, has no project branch, shares its open base branch with another night, or any ticket under a spec using that base remains open. Conflict or red checks push and delete nothing. Once `spec.merged` exists, another run performs only unfinished cleanup.
_Avoid_: finish (bare), summary (for this)
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**open-ticket**:
`dispatch.sh open-ticket <n>`: what `open` is for one ticket outside a night. The relay opens a watch on ticket `<n>` alone with the calling session as its main agent; nothing is written on the ticket. A ticket a night's watch already covers is refused. `land <n>` closes that watch once nothing works the ticket any more. Exit 0 opened; exit 2 nothing opened.
_Home_: `mmw-v2/skills/dispatch/references/one-ticket.md`

**start**:
`dispatch.sh start <n> worker|reviewer|verifier`: one ticket, one agent. Tonight's runner — `MMW_RUNNER`, `runner` in `MMW_HOME/models.json`, the runner the caller runs in when an adapter exists and the saved value is `auto`, then `orca` — starts the session through its adapter, with the agent's saved row resolved against that runner's catalog; `start` writes the session's started event on the ticket and prints the session id. Before it reads or creates a ticket branch it fetches `origin`; the base branch is the newest `worker.started.into`, else the open night's `spec.opened.into`, else the current checkout branch, and `origin/<base branch>` must exist. After the start, the adapter is asked to associate the absolute worktree path with the ticket; failure is reported once and the start remains successful. A start the runner refuses is refused once: no retry, no other host. On a ticket whose events still show a live worker, `start <n> worker` replaces it: that session is stopped through its own runner, `worker.replaced` names it, and the new worker starts in the same workspace; a worker that will not stop is refused and nothing starts beside it. A worker started in a standing workspace an earlier worker of the ticket left with uncommitted edits first commits them on the ticket branch and pushes it, and a start whose edits cannot be committed or whose push is rejected is refused. A start takes no product slot. A session whose started event the tracker will not take is stopped again and the start refused, since no command could find it. The worker row is chosen by the ticket's `junior-worker` / `senior-worker` label; a replacement worker keeps the first `worker.started.base`, and a reviewer gets the base commit computed from `origin/<base branch>` and the ticket branch; the verifier's first prompt names the `verdict` skill and the ticket. A ticket no running relay watches is refused too: its result would wake nobody. It cuts the worktree under the main checkout whichever worktree it is run from, so a worker starts its reviewer and verifier from its own worktree. Exit 0 started; exit 2 refused (`REFUSE`, reason on stderr), nothing started.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**adopt**:
`dispatch.sh adopt <n> [--into <branch>]`: the calling session becomes ticket `<n>`'s worker, for a session that picked the ticket up itself and was started by no `start`. Run from the ticket's worktree on `issue-<n>`, before claiming, it writes `worker.started` with the session's own runner and session (its adapter's `self`) and the facts `start` writes — the grade's `models.json` row, the machine, the worktree, branch and base — plus `adopted: true`, takes no product slot, and makes sure a relay watches the ticket: the watch already covering it, or a watch of the ticket alone with this session as its main agent. Inside an open night the base branch comes from `spec.opened.into`; outside one, with no prior `worker.started.into`, `--into <branch>` is required and that branch must exist on origin. A session that adopted a ticket outside a night is its own main agent, so it hands `land <n>` to the user rather than running it from the ticket's worktree. The same session adopting again writes nothing; a ticket another live worker holds is refused. Without it no event names the session, so its reviewer's report would wake nobody and `start <n> reviewer` would refuse. Exit 0 adopted, the session id on stdout; exit 2 refused.
_Avoid_: claim (for this; claiming is `--preflight`)
_Home_: `mmw-v2/skills/dispatch/references/inside-a-ticket.md`

**self**:
The `self` verb of a runner's adapter, and `dispatch.sh self`: the runner and session the calling process itself runs in, as `runner<TAB>session`. Each adapter reads its own runner's mark on the process — Paseo's `PASEO_AGENT_ID`, Orca's `ORCA_TERMINAL_HANDLE`, the name `herdr agent list` gives the agent in Herdr's `HERDR_PANE_ID` — and answers 0 with the id, 3 when the process runs in none of its sessions, 1 when it does and the id cannot be read (a Herdr agent with no name, an Orca terminal with no handle). `dispatch.sh self` asks the innermost runner first — Paseo, then Herdr, then Orca — since a wake sent to an outer terminal is typed into whatever it shows, and it is answered before `models.json` is even read, so it needs none. `open`, `open-ticket`, `adopt` and `ack` name the calling session with it, and `verify-ticket.py` names the session a `ticket.refused` is written by.
_Home_: `mmw-v2/skills/dispatch/scripts/runners/`

**retract**:
`dispatch.sh retract <n>`: take back what `start` left once the ticket's session is gone — commit what its worker left uncommitted on the ticket branch and push that branch to origin, archive the workspace, give back the product slot if its worktree holds one, give the claim back if this pipeline holds it, then write `worker.retracted`, which ends that session's hold so `advance` can start the ticket again. A session its runner still shows alive, or cannot answer for, is refused: that is a running worker, not a failed start; so is a ticket whose events cannot be read, and a push that is rejected, which leaves worktree, slot and claim standing and never forces. It does not merge. The branch stays, so the next `start` reuses it.
_Avoid_: abort (as the name of this), 撤销 (as a term)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**wait**:
`dispatch.sh wait <n> worker|reviewer|verifier`: reads the newest result event of an agent one started — `ticket.passed` or `ticket.returned` for a worker, `reviewer.reported` for a reviewer, `verifier.passed` or `verifier.failed` for a verifier — and prints its name and key fields (`verifier.failed commit=<commit> failed=AC2 ran=true`), never its prose. It reads the ticket once and asks no runner. Exit 0 result printed; 2 no started event of that kind, the comments could not be read, or an unreadable event; 3 no result of that kind yet. It is a read of the result, run after a **wake** has said the result is there; it is not how anyone learns a result, and a `3` is not a reason to run it again: the caller ends its turn and is woken. It writes nothing.
_Avoid_: paseo wait (in skill text, for this), 等待 (as a term)
_Home_: `mmw-v2/skills/dispatch/references/inside-a-ticket.md`

**resume**:
`dispatch.sh resume <n> "<text>"`: finds the worker session in the ticket's newest `worker.started` event and has the runner it names deliver the text (the adapter's `send`), then writes `worker.resumed`. Exit 0 the text was delivered; exit 4 the session was handed the text and its runner cannot show a turn starting — the text is in the session and is not sent again; exit 3 the worker is there and did not take it, or the runner could not tell — most likely a turn in progress, and so a reason to wait and run the same command again; exit 2 no `worker.started` event, the ticket's events could not be read, or the runner has no such session, nothing sent. Which of these it is, is the adapter's answer, never a reading of the runner's error sentence.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**status**:
`dispatch.sh status <spec>`: prints the `status.py --table` view. Exit 0; exit 2 when the table could not be computed, with one `dispatch: …` line on stderr and no table. Columns: `ticket`, `runner`, `session`, `worker`, `since`, `phase`, `ac`, `note`. Every row is the fold of that ticket's events and no runner is asked, so a session on any runner or any machine shows: `runner` and `session` name the ticket's newest worker, `worker` is `live` or the event that ended its hold, `since` is when it was started, `phase` the newest event's name, `ac` the `<met>/<total>` of the newest `ticket.checked` of the criteria, the worker's own or a reverify. A `note` of `events unreadable: …` names an unreadable event; `claimed, no session started yet` a `ticket.claimed` no started event has followed; `<k> live workers: …` more than one start still holding the ticket; `waiting for a product slot since <time> (<reason>, <k> of <max> held)` a `worker.queued` whose wait has not ended.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**`dispatch.sh reverify`**:
`dispatch.sh reverify <spec>`: fetches origin, resets the detached merge worktree to `origin/<base branch>`, and there runs every ticket under the spec whose events show it passed and landed (`status.py --reverify-plan`) through `verify-ticket.py <n> --reverify --actor main`, with `MMW_BASE_REF` set, every `--tools` directory forwarded, and the resulting `ticket.checked.commit` equal to that fetched commit. One that passed and has not landed is named and not run. Exit 0 all green; exit 1 reopens each red ticket for triage and writes `ticket.regressed`; exit 2 means a run could not establish a result, so nothing was judged on it and the rest are skipped.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**summary**:
`dispatch.sh summary <spec>`: posts the `spec.closed` event on the spec, first line `NIGHT SUMMARY <date>`, then closes the spec's watch, and the relay ends with its last. If `reverify` ran in this checkout, a `Reverify: <green>/<red>` line is appended. Exit 0 posted and no relay watches the spec; exit 1 posted and the watch closed, but the relay, which watched nothing else, did not end (its pid on stderr); exit 2 it could not be posted.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**status.py**:
`scripts/status.py` of the dispatch skill, six read-only forms: `--table <spec>` (the `status` table), `--advance-plan <spec>` (what `advance` has to do, in order), `--reverify-plan <spec>` (the landed tickets `reverify` runs), `--land-plan <n>…` (what `land` has to do), `--worker-grades <spec>` (the worker-grade labels of every ticket in the queue), `--summary <spec>` (prints the night summary; does not post it). Its one source is the tracker: the spec's tree of tickets and their children, read in one query by `tree.py`, and each ticket's state, labels, assignees, blocking links and comments. Where a ticket stands — which sessions were started on it and on which runner, whether it is held, passed, landed or returned — is the fold, through `events.py`; no runner is asked. It keeps no state file. The criteria count comes off the newest `ticket.checked` of the criteria.
_Avoid_: board.py, board
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**phase**:
The `phase` column of `status`: the name of the ticket's newest event, `closed` on a `CLOSED` ticket that carries none, or `-`. It is shown and never decided on; what a script decides from is the fold.
_Avoid_: stage (for this), selfcheck, implement (as a phase), closeout-rejected, handoff (as a phase)
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**`RELEASE`**:
The line `status.py --advance-plan` prints for a ticket whose claim is to be given back, between the `MERGE` lines and the `DISPATCH` lines, and which `dispatch.sh advance` carries out as `gh issue edit <n> --remove-assignee @me`. Four conditions together: the ticket is open, it is in the agent queue, this pipeline's own account is on it, and an event on it has ended every hold on it — so its worker is gone, whichever runner and machine it ran on. A claim no event ever showed held is kept, and so is the claim on a ticket with an unreadable event; each prints why on stderr. `advance` follows the write with a `ticket.released` event, reason `worker-lost`. A standing workspace is not a run: a worker holds its ticket only while its events show it live. A ticket usually carries a `RELEASE` and a `DISPATCH` of the same plan, since the claim is what kept it off the frontier and the frontier is read after the releases above it; `start` then reuses the standing workspace. Each one prints a line of its own. It is not `lease.py release`, and not `.mmw/target.json`'s `release` capability.
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**advance**:
`dispatch.sh advance <spec>`: lands the batch's passed tickets onto their recorded branch on origin, deletes each landed **ticket branch**, gives back claims whose holds ended, then starts the frontier — reading the plan a second time, after the merges and releases, for what to start. It refuses a night no relay watches, stops the sessions of a `ticket.returned` before it begins, and sweeps orphan merge worktrees after. A merge conflict or red repository checks are not a failure of the command: that ticket is reopened for triage as `ticket.bounced` and the rest carry on. Its summary line is `advance #<spec>: merged <m>, already in <s>, bounced <b>, released <g>, started <k>, refused <r>`; a runner that refused a start is exit 4, not exit 0, since a refusal read as success ends the main agent's turn with nothing left to wake it.
_Avoid_: 并回来 (as a term)
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**land**:
`dispatch.sh land <n>`: the one-ticket form of **advance** that lands the recorded commit, deletes its **ticket branch**, releases its resources and closes its watch.
_Avoid_: 落地 (as a term), 收尾 (that is the worker's closing steps), archive the ticket, finish (as a name)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**suspend**:
`dispatch.sh suspend <spec>`, the decision to give a night up before it is over, taken when the fault is in the pipeline rather than in a ticket. It stops every session still holding a ticket of the batch — its worker, and a reviewer or verifier whose result is not in — through that session's runner's `stop`, which interrupts it mid-turn, unless the runner already shows it stopped; then it commits tracked edits and pushes each stopped ticket branch to origin before releasing anything, and leaves the workspace and the branch standing. It posts `spec.suspended` on the spec and on every ticket still in the agent queue, gives back every claim with a `ticket.released` event (reason `suspended`), gives back every lease slot the batch holds, and closes the spec's watch. That is what lets `advance` take the same batch up again once the fault is fixed: each ticket is unclaimed, no agent holds it, and its standing workspace is reused. A ticket one of whose sessions could not be stopped, whose edits could not be committed, whose push was rejected, or whose events cannot be read is left exactly as it was and named on stderr; no force-push is ever attempted. `lease.py` refuses a slot something still listens on, and `suspend` reports that on stderr and exits 1 rather than forcing it. Exit 0 when nothing was left over, 1 when something was, 2 when nothing was touched. `ABANDON:` on a criterion is unrelated: it says one criterion was given up, and this says a night was.
_Avoid_: abandon (as the name of this), 收夜, give the night up (as a name)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

### The night

**night**:
Everything between the last ticket published and the morning: the user says it starts, the main agent runs `check`, then `open`, then — once, before the first `advance`, when the batch drives a screen contract — the batch lint, then `advance`, and ends its turn; on each **wake** it reads `status`, decides — `resume`, `retract`, or reading a stopped session on the runner its `worker.started` event names — runs `advance` once, and acks the wake. A ticket leaves the night by its worker's closing comment, or by staying in the agent queue behind an open blocker all night, which the `Not dispatched, a blocker stayed open:` line of `NIGHT SUMMARY` lists. The night ends when the frontier is empty and `status` shows no live agent: then the **收口轮** if open `finding` children remain, then `reverify`, then `summary`, which closes the night's watch — and, only after the user accepts the result, `finish`.
_Avoid_: 夜间编排主循环, night orchestration loop, 夜里 (as a term), 夜间 (as a term), run (as the command that opens a night)
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**收口轮**:
The pass the main agent runs when the frontier is empty and this spec's tickets still hold open `finding` children — the ones whose `child.opened` no `child.closed` has followed: route exactly those by the 门槛, commit the ones it fixes under the three rules listed beside them, open as few tickets as possible for the ones that become tickets (a ticket whose files sit in another live ticket's `## Owns` is `Blocked by` that ticket), record where each went with **route**, then `advance`, and loop until none survive. It sits between the empty frontier and `reverify` in `night.md`.
_Admitted_: closing pass
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**route**:
`dispatch.sh route <ticket> <child> fixed|stale|became-ticket [<new ticket>]`: the one way a `finding` leaves the closing pass. `<ticket>` is the ticket whose `child.opened` names the finding, and the spec is the one that event names — never read off the tree, which a `became-ticket` route itself changes. It closes the finding (`fixed` as completed, `stale` as not planned) or makes it a ticket, then writes `child.closed` on `<ticket>`, the one record of where the finding went. In place — `<new ticket>` is the finding itself — the finding stays open, its `mmw:child` becomes `mmw:ticket`, and its parent moves from the ticket to the spec, since the scripts find a ticket's spec through its direct parent alone; folded into another issue, the finding is closed as that issue's duplicate and that issue gets the same label and parent. Run again, it finishes what the tracker left undone without doing any step twice, and a route already recorded that way exits 0.
_Avoid_: re-parent (as the name of this), promote
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**门槛**:
The four steps, and the check before them, that decide whether a `finding` child is worth a ticket. They run in order, first match wins; the default is that the main agent fixes it. They are written in `night.md` step 4, where they are executed: a night runs in a consuming repository, which has no copy of this repository's `docs/`. ADR 0012 records why the thresholds fall where they do, not how to apply them.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

### Liveness

**relay**:
`scripts/relay.py` of the dispatch skill: it turns events on the tracker into wake-ups for the session waiting on them. Every `--interval` seconds (default 30) it reads the comments of every ticket its **watches** cover — tickets outside a night, or the sub-issues of a night's spec, listed again every cycle — and for each event its `WAKES` table names writes one row into the wake queue and hands that row to the runner of the session it names. It reads a ticket in full when it starts, since a relay that was down cannot assume it missed nothing. It decides nothing — whether to advance, resume, retract or stop stays the main agent's — and writes nothing to the tracker: its only writes are files in the state directory. A stretch with no good poll longer than `--grace` (default three intervals) is announced once to every watch's main agent, as a `relay.recovered` row ahead of the events it recovered. When an event that gives a product slot back lands on any watched ticket, every watched ticket still waiting under an older `worker.queued` gets one `worker.queued` row for its worker. One relay runs per repository, holding `relay.lock`, and carries every watch in `watches.json`. `relay.py start` opens a watch — refusing, with nothing written, a session its runner shows stopped or a watch that shares a ticket with an open one — and runs the relay detached when none runs; `add` is the same checks and write without the process; `stop` closes one watch (or every watch when none is named) and ends the process with the last (forgetting the last good poll, so the next start announces no stretch for a closed night); `watching` says whether it sees a ticket. Every ten cycles it asks each watch's main agent's runner `liveness`, and closes the watch of one answered `stopped` at every ask for an hour. `dispatch.sh open`, `open-ticket` and `adopt` open watches; `summary`, `suspend` and `land` close them.
_Avoid_: board.py, board, watcher (as a name)
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**watch**:
What the relay reads and whom it wakes about it: a night's spec, whose sub-issues are listed again every cycle, or tickets outside a night. `open`, `open-ticket` and `adopt` open one with the calling session as its **main agent**, and `watches.json` in the state directory keeps it under `spec:<n>` or `tickets:<n>[,<n>...]`. Two watches never share a ticket, so a ticket's main-agent wakes have one recipient; a ticket that comes to sit under a watched spec after both were opened stays with its tickets watch. It is closed by `summary`, `suspend` or `land`, or by the relay itself when its main agent's runner has answered `stopped` at every ask for an hour.
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**wake queue**:
The file `queue.jsonl` in the state directory: the relay's **rows**, one JSON object per line in sequence order. A row is one wake-up — `seq` (increasing across all recipients, never reused), `ticket`, `event`, `to` (`worker` or `main`), the `watch` its ticket belongs to, the recipient's `runner` and `session`, `at` — and what is sent for it is `#<ticket> <event>` through the runner's `send`, nothing more; what happened is read on the ticket. The send's answer decides the row: `0` delivered and kept until acked; `4` handed over with no turn start seen, marked delivered and `unconfirmed`, kept until acked and not typed again until the relay restarts; `3` nothing was sent (the recipient is in a turn, or its runner could not be asked) and kept for the next cycle; `2` no such session and dropped; anything else, including a send that could not be run, kept. A row is dropped without a send when its watch was closed, when its recipient is no longer the current one for its role, or when it is a `worker.queued` wake and its ticket no longer waits for a slot; every drop is named on stderr. A recipient's rows reach it in sequence order, and a row that stays holds back only that recipient. Only an ack removes a row, so a row sent twice — every unacked row is sent again when the relay starts — is still handled once. `relay.py queue` prints the rows, and exits 3 when no relay has polled within its grace.
_Admitted_: row (one entry of it), wake-up
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**recipient**:
The session a row of the wake queue is for, always named by its (runner, session) pair and never by the session id alone. For `reviewer.reported`, `verifier.passed`, `verifier.failed`, `reviewer.lost` and `verifier.lost` it is the worker that started that reviewer or verifier: the `runner` and `session` of the ticket's latest `worker.started` before the event, so a worker needs no registration. For a `worker.queued` wake it is the ticket's latest worker the same way. For `ticket.passed`, `ticket.returned`, `ticket.refused`, `child.opened` of kind `fault` or `decision` and `worker.lost` it is the main agent of the watch the ticket belongs to, as the `relay.py start` that opened that watch recorded it in `watches.json`; `relay.recovered` goes to every watch's main agent. Opening a watch is the only way a main agent is named.
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**ack**:
A recipient saying it has handled its rows: `relay.py ack --runner <runner> --session <session>` with `--through <seq>`, or with the wake as it arrived — `--ticket <n> --event <event>`, or `--event relay.recovered` — which acks through that recipient's oldest delivered row naming it. `dispatch.sh ack <n> <event>` (or `ack relay.recovered`) is the second form for the calling session, named by `self`. It removes that recipient's rows up to that point and nobody else's; a sequence number never issued, or a wake with no row queued for that runner and session — acked already, sent to another session, never queued — is refused, naming what it looked for and what is queued for that session. Delivering a row never removes it; only this does. The main agent acks after its one `advance` for the wake; a worker after reading the event.
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**state directory**:
`$MMW_HOME/state/<owner>__<name>/` — `MMW_HOME` defaults to `~/.mmw`, the root `lease.py` keeps its registry under — one per repository, owner and name lowercased, created with mode 0700. It holds every file a long-running MMW process keeps about that repository on this machine, and nothing about it is kept anywhere else. The relay's files there are `queue.jsonl`, `queue.seq`, `queue.lock`, `seen.json`, `watches.json` (every open watch and its main agent; it outlives the process), `beat.json`, `gap.json`, `relay.lock`, `relay.json` (the running relay's pid and identity) and `relay.log` (what started relays printed); the watchdog's are `watchdog.lock`, `watchdog.json` (its **heartbeat**) and `watchdog.log`; the turn guard's is `guard.log`; and `dispatch.sh` keeps one `merge-<slug>.lock` per merge target beside them. A file in it is replaced in one step, so a reader sees the old one or the new one, and a file that is there but is not JSON is refused rather than read as absent.
_Avoid_: state file (for a ticket's state; that is the fold)
_Home_: `mmw-v2/skills/dispatch/scripts/statedir.py`

**lock record**:
What a lock file in the state directory holds while its lock is taken: one JSON object with the holder's `pid`, its process `identity`, `since` and `purpose`. The kernel's `flock` on the file is what excludes; the record only says who is in there, for a reader that will not take the lock — a shell script, a watchdog, a refusal that has to name the holder. A pid alone does not name a process, because the system hands a dead process's pid to the next one, so the record names a live holder only when its pid runs now **and** that process's identity — its start time as `ps -o lstart=` prints it, in UTC and the C locale — is the recorded one. A record that fails either is stale and names nobody; the kernel let go of the lock when its holder died, and the next holder overwrites it. A holder that exits normally empties it.
_Admitted_: process identity (for the start time)
_Home_: `mmw-v2/skills/dispatch/scripts/statedir.py`

**watchdog**:
`scripts/watchdog.py` of the dispatch skill: the second and third layers of liveness, one process per repository while a watch is open, not an agent and spending no tokens. It holds `watchdog.lock` for as long as it runs and writes its **heartbeat** every round (default every 60 seconds). Each round it checks the **relay** — its lock record names a live process, its last good poll is within its grace — and folds every ticket the relay's watches cover, less the closed sub-issues of a night's spec: a closed ticket's worker has handed in its work. For a ticket that is held and has had no event for `--silence` seconds (default 600), and every round for a ticket in the waiting step (the fold's `waiting`: quiet by design, so its silence proves nothing, and still not exempt), it asks each session still holding it — the worker, and a reviewer or verifier whose result is not on the ticket after its start — whether it is alive, through that session's own runner's `liveness` and no other runner's, and only when the session's `*.started` names this machine (`machine`, the hostname): `alive` does nothing; `stopped` posts `worker.lost`, `reviewer.lost` or `verifier.lost` naming that (runner, session) — the only events not written by the agent they are about, and this process is their one writer; `unknown` is recorded in the heartbeat and reported, never taken for alive and never a `*.lost`. A held ticket silent for `--idle` seconds (default 3600) whose worker's runner answers `alive` and that waits on nothing — no live reviewer or verifier, no product slot, no pass — is a finding too: that worker ended its turn with nothing to wake it. What it finds besides a stopped session — the relay down, a runner that could not say or a session on another machine, a held ticket with no session to ask, such an idle worker, events that cannot be read, the board unread past its tolerance — it sends itself, through the `send` of the runner the main agent runs in: a finding about a ticket to the main agent of that ticket's watch, `relay down` and the unread board to every watch's main agent, one line whose findings each begin `watchdog:`, each finding once: not a wake, not a row of the wake queue, never acked. A send that started a turn ends it, and that turn's end re-arms it through the **turn guard**. `watchdog.py arm` starts it unless it is healthy; `status` prints the heartbeat.
_Avoid_: watcher, heartbeat (for the process), board.py, judge (as a name for the script)
_Home_: `mmw-v2/skills/dispatch/scripts/watchdog.py`

**heartbeat**:
`watchdog.json` in the state directory: what the **watchdog** writes at start, after every ticket and at the end of every round — its `pid`, process `identity` and `machine`, `at`, `poll`, `tolerance`, `silence`, `idle`, the watches it read with their main agents, the tickets `held` and `waiting` at its last round (`held` is null when that round could not read every ticket), the sessions whose runner answered `unknown`, the `*.lost` it posted, the relay's problem if any, `read_at` and `read_failure` for its last whole read of the board, the findings `pending` and `reported`, `main` (per main agent, why its findings could not be sent), `closed`, and `reads`, its billed and not-modified comment-list reads since it started. The watchdog is **healthy** when its `watchdog.lock` names a live process by pid and identity, that same process wrote the heartbeat, the heartbeat is no older than its **tolerance**, and its last whole read of the board is within that tolerance too — a watchdog that cannot read the board watches nothing. A heartbeat another process wrote proves nothing about the one holding the lock.
_Avoid_: `mmw-night-<spec>`, beat (for this file; the relay's `beat.json` is its last good poll)
_Home_: `mmw-v2/skills/dispatch/scripts/watchdog.py`

**tolerance**:
How old a heartbeat may be and still be fresh, and how long the board may go unread: `max(300, poll + margin)` seconds, the margin being one adapter call plus one list read, every page of one address together (60 + 120), the longest a watchdog waits between two beats. A fixed number would read a healthy watchdog as dead mid-sleep as soon as its poll grew past it, and a smaller margin would have `arm` end one that is only slow. For a runner, the tolerance of a `stopped` answer is how long a dead session may still read `alive`; the Herdr adapter records its measured value (1 second) in its header.
_Home_: `mmw-v2/skills/dispatch/scripts/watchdog.py`

**turn guard**:
`scripts/turn-guard.py` of the dispatch skill, the first layer of liveness: a hook `install.sh` registers on the turn-end event of all five hosts (`Stop` for Claude, Codex and Grok, `stop` for Cursor, `agent_settled` through an extension for Pi). It acts only in a session that is the main agent of an open watch in `watches.json`: that watch's runner's `self` must answer this session's id, and anything it cannot establish — no watch, no adapter, a `self` that cannot answer — means it is not a main agent and nothing is held. It arms the **watchdog** when it is not healthy and, when tickets are held and the watchdog still is not healthy, keeps the turn from ending — exit 2 on Claude, Codex and Grok; one follow-up message on Cursor and Pi, which cannot hold a turn — once per turn end, with the one command to run. The copy registered for Claude stands down when `GROK_AGENT` or `GROK_HOOK_EVENT` is set and when the payload carries Cursor's `cursor_version`, and never on `GROK_SESSION_ID`; the copy registered for Cursor acts only on a payload with `cursor_version`. Every decision it makes is appended to `guard.log` in the state directory. What each host was seen to do is recorded in the script's header.
_Avoid_: stop hook (as its name), turnend guard, auto-arm
_Home_: `mmw-v2/skills/dispatch/scripts/turn-guard.py`

### Values at a glance

| name | values |
| --- | --- |
| `phase` | the newest event's name · `closed` · `-` |
| `status.py` columns | `ticket` · `runner` · `session` · `worker` · `since` · `phase` · `ac` · `note` |
| `note` | `ready` · `waiting on #<m>` · `(passed, not landed)` after a blocker · `<k> live workers: …` · `events unreadable: …` · `claimed, no session started yet` · `waiting for a product slot since <time> (<reason>, <k> of <max> held)` · newest event's first line · empty while a worker holds it |
| relay wakes the worker | `reviewer.reported` · `verifier.passed` · `verifier.failed` · `reviewer.lost` · `verifier.lost` · `worker.queued` (a slot given back) |
| relay wakes the main agent of the ticket's watch | `ticket.passed` · `ticket.returned` · `ticket.refused` · `child.opened` (kind `fault` or `decision`) · `worker.lost` · `relay.recovered` |
| relay send answer | `0` delivered · `4` handed over, unconfirmed (treated as delivered) · `3` nothing sent · `2` no such session · other kept |
| watchdog finding | `relay down` · `liveness unknown` (the runner could not say, or the session was started on another machine) · `held with no session to ask` · `silent … with nothing to wait on` (an idle worker) · `events unreadable` · `cannot read the board` |
| turn-end event (turn guard) | Claude, Codex, Grok `Stop` (exit 2 holds the turn) · Cursor `stop` (`followup_message`) · Pi `agent_settled` (follow-up) |
| finish notification | `finished` · `errored` · `was closed` · `needs permission` |
| runner (one adapter each) | `paseo` · `orca` · `herdr` |
| adapter verb | `start` · `send` · `liveness` · `stop` · `self` · optional `attach` · optional `open-url` · Paseo only: `catalog-status` · `catalog-models` · `diagnostic` |
| `liveness` answer | `alive` · `stopped` · `unknown` |
| advance plan line | `MERGE <n>` · `RELEASE <n>` · `DISPATCH <n>` |
| `dispatch.sh` constants | `DEFAULT_WORKER = junior-worker` · `MERGE_TRIES = 3` · `OWN_RUNNERS = paseo herdr orca` |
| `dispatch.sh` verbs | `board` · `check` · `open` · `open-ticket` · `adopt` · `self` · `advance` · `integrate` · `land` · `start` · `retract` · `wait` · `ack` · `resume` · `status` · `reverify` · `summary` · `finish` · `suspend` · `route` |
| `relay.py` verbs | `run` · `start` · `add` · `stop` · `watching` · `ack` · `queue` |
