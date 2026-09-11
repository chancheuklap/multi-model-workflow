# Ticket run

One ticket from claim to close: the sessions that work and judge it, the events they leave on it, the runs of its criteria, the code review, the verdict, the advisor, the closing steps and the gate that closes it. It exists because everything this part of the pipeline knows is written on the ticket, and every word it writes there has to mean the same thing to the next session that reads it with an empty context.

How to read an entry: the bold line is the term's only name; a term whose name is a literal string that appears in a file, a command, or a comment is named by that string exactly (case, colon, and all). The definition says what the thing is and what sets it apart from its neighbours. `_Admitted_` lists the one other wording that may appear in prose. `_Avoid_` lists dead words: a sentence in this repository that uses one is wrong; an item followed by a note in parentheses says in which sense the word is dead. `_Home_` is the file whose text or code the definition is taken from; when this file and that one disagree, that one is right and this file is rewritten. An attribute that can be had by reading that file — a field list, an exit code, a command's switches, the branches of a behaviour — is not repeated here: an entry says what the term is and how it differs from its neighbours, and points at `_Home_` for the rest.

## Language

### Roles

**worker**:
An independent session dispatched to do one ticket, running the whole path from claiming the ticket to writing the closing comment. It runs the `implement` skill — its prompt is `Use the implement skill to work ticket #<n>.` plus the three standing sentences `start` gives a worker (work autonomously, the `drive-target` skill's five rules while the product is running, and report a pipeline fault rather than work around it); its only input is the ticket; it owns the `issue-<n>` workspace, worktree and branch; it starts its verifier and its reviewer; it never closes the ticket by hand.
_Admitted_: worker session
_Avoid_: 工人, 做票的 agent, 领票的 agent, MMW_TICKET
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**reviewer**:
The session a worker starts with `dispatch.sh start <n> reviewer` to run one round of code review. Its prompt names the `code-review` skill, the ticket, and the base commit `start` computes from `origin/<base branch>` and the ticket branch, plus the one standing sentence about working autonomously. It runs in the ticket's worktree, the worker's own, and cuts no branch; its report is the **review comment**, which the worker reads off the ticket. The worker does not stop it: landing does, together with every other session the ticket's started events name, when it archives the workspace (`land <n>` for one ticket, `advance` for a batch). On its own, `reviewer` always means this session, never one of the three axis subagents.
_Admitted_: reviewer session
_Avoid_: reviewer 会话, code-review 会话, 审稿人, MMW_AUTONOMOUS
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**dispatcher**:
The role the reviewer session takes once it holds the `code-review` skill: it starts the three axis subagents, sorts every review finding into in-ticket or out-of-ticket by the six conditions in `references/session.md` section 3, and writes the one review comment. It reviews nothing and fixes nothing itself. The session reads `references/session.md`; each axis takes the matching axis door of the same skill. `SKILL.md` is the shared door.
_Avoid_: 派发 (as a term)者
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**verifier**:
The session a worker starts last of its closing steps, once, with the prompt `Use the verdict skill to verify ticket #<n>.` plus the two standing sentences `start` gives a verifier: work autonomously, and read the `drive-target` skill's five rules while the product is running before reaching or stopping it. In the same worktree on the same commit it re-runs every acceptance criterion with `--reverify` and posts one verdict with `verify-ticket.py <n> --verdict`: a `verifier.passed` or `verifier.failed` event. It runs after the last commit, because `--closeout` requires the verdict's commit to be `HEAD`; that one round is the whole of it, and a `verifier.failed` ends in a `HANDOFF REQUIRED`. It may repair its own environment and changes no file in the repository; it never starts the product by hand and never writes an `ABANDON:` line.
_Avoid_: 复验者, verifier 子代理, subagent verifier
_Home_: `mmw-v2/skills/verdict/SKILL.md`

**advisor**:
The second-opinion agent on a stronger model; it implements nothing. One door: a session from the advisor row of `models.json`, started by whichever agent hit the decision with its host's `create_agent` tool, its first prompt the line `Use the advisor skill.` followed by the **question packet**; how it is started, and what an agent with no such tool does instead, is the skill's `references/consulting.md`. Nothing but its own instructions holds it to reading — a session on any host can write through a shell.
_Home_: `mmw-v2/skills/advisor/SKILL.md`

**question packet**:
What a caller hands the advisor, and the only thing the advisor sees — not the caller's session, not its tool trace: the recent user/assistant exchange quoted, the caller's current understanding, the constraints it believes bind, the options it weighed and which way it is leaning, and the file paths it believes relevant. It carries the decision and the evidence; what to read and what to conclude stay the advisor's, so the list of what to check, the file to skip, the conclusion expected confirmed, and the narrowing of "which option" to one option's details stay out of it.
_Avoid_: 问题包, advisor prompt, brief
_Home_: `mmw-v2/skills/advisor/references/consulting.md`

**recommendation**:
What one consultation of the advisor gives back: do X, not Y, because Z, plus the single risk that decides it — or, when the caller's reading is sound, that it is sound and the one thing to watch. Missing information that would change the answer is named exactly, with what each answer would imply.
_Avoid_: verdict (for this)
_Home_: `mmw-v2/skills/advisor/references/advising.md`

### Comments on the ticket

**ticket comment**:
One comment a script or an agent leaves on the ticket. Every one a script leaves is an **event**, and an event block is the only part of any comment a program reads: a run of the criteria, the files another ticket changed, a wait for a product slot and a failed repository check are events like the rest. A comment an agent types — a `## Seam` it derived, a note on a wrong `CHECK:` — is prose, which no program reads. The ticket's comments are its only run state.
_Avoid_: 票评论, COMMENT (as a kind label), `self-run`, `reverify`, `TOUCHED BY`, `CHECKS FAILED` (each as a comment found by its first line)
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**event**:
One comment that records one thing that happened, in two parts: a first line and any prose after it, for a person, and a trailing `<!-- mmw {...} -->` block — one line of JSON, invisible on GitHub — which is the whole of what a program reads. Its name is `subject.verb`: a subject from `spec`, `ticket`, `worker`, `reviewer`, `verifier`, `child`, a verb in the past tense, lower case, and never a value inside the name — ticket numbers, commits, hosts and models are fields of the payload. Every payload carries `v`, `event`, `stage`, `actor`, `spec`, `ticket` and `at`; which further fields each event requires, which take a closed set of values, which must match a shape, and which come only as a group, is the table `EVENTS`. Every event is posted by a script — `verify-ticket.py`, or `dispatch.sh` through `events.py emit` — and never typed by a model, so a `VERDICT` written with `gh issue comment` carries no event and counts for nothing. Prose that quotes an event has its opener turned into visible text (`neutralise`), so a comment carries no block but its own.
_Admitted_: event block (the trailing block alone)
_Avoid_: protocol comment, status word, marker line
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**fold**:
A ticket's state, computed and stored nowhere: the issue's comments read in comment-id order and their events replayed from an empty state. The order is by id, never by timestamp, because two comments written in the same second carry the same one; an edited comment counts in its newest version. The replay starts from empty every time and never updates a state it computed before, because state goes backwards — `ticket.regressed` takes back a pass and a landing, `ticket.released` a claim, `worker.retracted` a start — and a replay needs no inverse for any of them. A comment with no block is prose and changes nothing, whatever its first line says. `events.py fold <issue>` prints it; `status.py`, `dispatch.sh`, `verify-ticket.py` and the relay read a ticket's events through `events.py` and nowhere else.
_Avoid_: phase inference, state file, incremental state
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**held**:
What the fold says of a ticket an agent may still be working: it stays off the frontier and `advance` does not give its claim back. A ticket is held from its `ticket.claimed` or any `worker.started`, `reviewer.started` or `verifier.started` until an event ends the hold. `ticket.landed`, `ticket.returned`, `ticket.bounced`, `ticket.released` and `spec.suspended` end every hold on it; `worker.retracted`, `worker.lost`, `worker.replaced`, `reviewer.lost`, `verifier.lost` and a `ticket.refused` that names its session end the one session they name, matched by its (runner, session) pair and never by the id alone, since two runners can hand out the same id; a retraction also ends a claim no started session has taken over; `worker.resumed` makes the session it names live again. A result ends the hold of the session that produced it: `reviewer.reported` that reviewer's, `verifier.passed` or `verifier.failed` that verifier's (the one it names, else the newest live one of that kind), so a finished reviewer never keeps a ticket whose worker is gone. `ticket.passed` ends none — the close after a pass can fail and leave the worker retrying — and no label ends one. It is the same answer whichever runner and machine the worker runs on. A worker that died with nothing ending its hold keeps its ticket held until the **watchdog** writes `worker.lost` — once the worker's own runner says its session has stopped — or `retract` writes `worker.retracted`; one whose runner cannot say stays held; a claim that no event ever showed held — one assigned by hand, say — is never given back by `advance`, since nothing shows its worker gone. A hold is not a product slot, which a worktree keeps until its ticket's work ends, past a replaced or lost worker (see **lease**).
_Admitted_: hold (the noun)
_Avoid_: live worker (as what keeps a ticket off the frontier), occupied, 占用 (as a term)
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**unreadable event**:
A comment carrying an `<!-- mmw` block the fold cannot read: never closed, two blocks in one comment, not JSON, a version other than 1, no event name, or a payload `EVENTS` refuses. It is never skipped as prose: the fold lists it under `unreadable`, and every command that decides from the fold refuses to decide about that ticket until a person fixes the comment — every reader of `events.py` but `fold` itself (`session`, `sessions`, `result`, `checked`, `live`, `child`) exits 3, `wait`, `resume` and `retract` refuse, `advance` neither merges, releases nor dispatches the ticket, `suspend` leaves it as it was, `--closeout` refuses, and `status` notes `events unreadable: …`.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**landed**:
What `status.py` calls a ticket that is `CLOSED` on the tracker and whose fold shows a `ticket.passed` with a `ticket.landed` after it: the passed commit is in `origin/<base branch>`, and the `ticket.landed` event records it — the branch, the base branch, the commit, and, when a merge brought it in, that merge and its first parent, whose compare and commit links open the whole-ticket diff. A pass posted after a landing takes the landing back, and so do `ticket.regressed` and `ticket.bounced`.
_Avoid_: closed (for this), merged (as the state of a ticket), done
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**first line**:
The first line of a ticket comment. On an event it is prose for a person, worded however its writer likes, and no program reads it: rewording it breaks nothing, and every comment a script posts is an event. Two first lines are a script's input before they are posted: `--closeout` reads a draft's `ALL MET` or `HANDOFF REQUIRED:` to post it as `ticket.passed` or `ticket.returned`, and `--review` reads a report's `REVIEW <base commit>..<HEAD commit>` for the event's two commits. `--sub-issue` takes a child's title from the first line of its file. A disclaimer goes last.
_Avoid_: 首行 (as a term), protocol slot, 协议位, status word, slot (bare — see **slot**)
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`worker.started`, `reviewer.started`, `verifier.started`**:
The event `dispatch.sh start` posts on the ticket once the runner has started the session. It writes the same field set for all three kinds: `session` (that runner's own id for it), `runner`, `machine` (the hostname the session was started on, because a runner answers only for its own machine), `host`, `model`, `effort` (`—` when the host takes none), `grade`, `worktree` (an absolute path), `branch`, `base` (the base commit) and `into` (the base branch); `EVENTS` requires all of them of a `worker.started` and `session`, `runner` and `machine` of the other two. It records no product slot: a worker takes one at its first run that needs the product, and that run's `ticket.checked` names it. It is the only record of the session: `resume`, `wait`, `retract`, `land` and `suspend` find the session in the newest such event of its kind and ask the runner it names, and no other, so every machine that reads the ticket gets the same answer. A session whose event cannot be written is stopped again and the start refused, so none runs where nothing can find it. Each one begins a hold.
_Admitted_: started event (any of the three), `*.started`
_Avoid_: RUNNER line, runner line
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`ticket.claimed`, `ticket.refused`**:
The two events `--preflight` posts, one or the other. `ticket.claimed` follows the claim and begins a hold; the assignee is the claim, so a claim whose event could not be written still stands, and stderr says so. `ticket.refused` carries the first refusal's `reason` — `wrong-branch`, `dirty-tree`, `not-open`, `not-ready`, `blocked`, `claimed-by-other` — and names the refusing session by `runner` and `session` together when it can name itself, so that session's own hold ends and the ticket is free for the next start; its first line is the `NOT_READY: …` sentence that `--preflight` also prints; exit 2, and the worker stops.
_Avoid_: NOT_READY (as the name of the refusal; `NOT_READY: …` is its first line and its printed text)
_Home_: `mmw-v2/skills/verify-ticket/references/claiming.md`

**`ticket.passed`, `ticket.returned`**:
The two events `--closeout` posts a closing comment as, each after the change it announces: `ticket.passed` for an accepted `ALL MET` draft, once the ticket is closed; `ticket.returned` for a `HANDOFF REQUIRED` draft, carrying each `ABANDON:` line, once the ticket is handed back. When the tracker does not make the change, neither is posted and the closeout is refused. `ticket.returned` ends every hold on the ticket; `ticket.passed` ends none. `advance` merges a `CLOSED` ticket whose `ticket.passed` no `ticket.landed` has followed; a pass after a landing is new work that has not landed yet. Each wakes the main agent; `wait <n> worker` prints one of the two.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`ticket.released`**:
The event that follows a claim given back by `land` (reason `landed`), `suspend` (`suspended`) or `advance`'s `RELEASE` (`worker-lost`). It ends every hold on the ticket.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`ticket.landed`**:
The event `dispatch.sh advance` and `dispatch.sh land` post on a ticket once its `ticket.passed` commit is in `origin/<base branch>`. It is written only after the push, so the record never runs ahead of the fact, and it is what lets the tickets this one blocks start: a ticket is cut from the base branch and has to find its blockers' work there, so closing the ticket is not that signal and landing is. It ends every hold on the ticket and gives its worktree's product slot back; what it records of the ticket is the **landed** state. A landing whose event could not be written leaves the tickets it blocks blocked until the next `advance` or `land` writes it.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`ticket.regressed`**:
The event `dispatch.sh reverify` posts on a landed ticket whose criteria went red on the base branch, with that `commit` and the `failed` criteria, in the same pass that reopens it, labels it `needs-triage` and removes its assignee. It takes back the ticket's pass and its landing.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`ticket.bounced`**:
The event that hands a passed ticket to triage when its landing merge conflicts (`reason` `conflict`) or its repository checks fail (`checks`). It records the failed attempt's evidence and the `commit` it was tried on, takes back pass and landing, ends every hold on the ticket and gives its product slot back, and leaves its workspace standing for triage.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`worker.resumed`, `worker.retracted`, `worker.replaced`, `worker.lost`**:
The events about one worker session after its start, each naming it by `runner` and `session` together. `resume` posts `worker.resumed` once the runner has taken the text, or handed it over without being able to show a turn starting (exit 4). `retract` posts `worker.retracted` once the runner shows the session gone, recording whether the workspace, the slot and the claim were given back. `start <n> worker` on a ticket whose events still show a live worker stops that session through its own runner and posts `worker.replaced` naming it, then the new session's `worker.started`; the worktree, the branch and the worktree's product slot carry over to the new worker, and what the old one left uncommitted is committed on the branch first (`wip(#<n>): uncommitted work of …`). `worker.lost` is not written by the agent it is about, since a dead agent cannot write its own: the **watchdog** posts it, actor `judge`, once the ticket has been silent past its silence and the session's own runner answers `stopped`; the relay wakes the main agent on it.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`reviewer.reported`**:
The event `verify-ticket.py <n> --review <file>` posts on the ticket, carrying the **review comment** and the `base` and `head` commits read off that comment's first line — a report that names no commits does not say which diff it read, so a file that does not open with them, or is empty, is refused and nothing is posted. It is the reviewer's whole output: `--review` tells nobody, and the **relay** is what turns the event into the worker's **wake**, so a report that lands is a report its worker hears about however the reviewer's own turns fell. It ends that one reviewer's hold and no other.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`reviewer.lost`, `verifier.lost`**:
A reviewer or verifier session that stopped before its result landed, named by `runner` and `session` together, the same shape as `worker.lost` and posted the same way, by the **watchdog**, actor `judge`: the ticket was silent past its silence, the session had no `reviewer.reported` (or verdict) after its own start, and its runner answered `stopped`. Each ends that one session's hold, and not the wait of a worker run in the waiting step. The relay wakes the ticket's worker on it — the worker waiting for that result — which starts another reviewer or verifier.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`spec.opened`, `spec.closed`**:
The two events that bracket a night on its spec. `dispatch.sh open <spec>` posts `spec.opened` once the watch is open and this session is the night's main agent, recording that main agent's runner and session, the base branch as `into` and the project branch as `project`; every later command reads those from it — `start` takes the base branch from it when no `worker.started` carries one, and `finish` refuses a spec whose `spec.opened` names neither. A night whose `spec.opened` could not be written is not open, and the watch that call opened is closed again. `dispatch.sh summary <spec>` posts `spec.closed` when the night is over, carrying the **`NIGHT SUMMARY`** comment and the night's `date`; `finish` refuses a spec that carries no `spec.closed`. Neither is `spec.merged`, which comes after the user has accepted the night's work.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`spec.suspended`**:
The event `dispatch.sh suspend <spec>` posts on the spec and on every ticket of the batch still open and in the agent queue, first line `NIGHT SUSPENDED #<spec>`. Under it: the time the night was suspended, that the ticket has no verdict, and either that its worker was interrupted (stopped through the runner its started event names) or that no session of ours was on it. It ends every hold on the ticket, so a ticket whose worker could not be stopped gets none: it would read as unheld while that worker still runs, and the next `advance` would start a second one beside it. Its reader is whoever opens the ticket the next morning and would otherwise find a batch with no verdict on any of it and no way to tell that from work in progress. A ticket handed back to triage during the night carries its own verdict and gets none.
_Avoid_: NIGHT SUSPENDED (as a name; it is the event's first line)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`child.opened`, `child.closed`**:
The events that record a ticket's children on the ticket itself. `--sub-issue <kind> <file>` posts `child.opened`: the new issue's number as `child`, its `kind` (one of the five **child kinds**), its title, and — as on every event — the ticket's `spec`; the child's own body opens with the line ``A `<kind>` child of #<n>.``, which is for a person. `child.closed` is what **route** posts on the ticket when it settles a `finding`: `resolution` `fixed`, `stale` or `became-ticket`, the new ticket in `became`. The closing pass, `route` and `NIGHT SUMMARY` take a child's kind, spec and route from these two events and from nothing on the child itself or on the tree, which a `became-ticket` route changes; a closed `finding` no `child.closed` accounts for is counted `unread`.
_Avoid_: SUB-ISSUE (as a name or as the first line of a child's body)
_Home_: `mmw-v2/skills/verify-ticket/references/sub-issues.md`

**child kind**:
What a child records, named for who can answer it rather than where it came from: the `kind` of its `child.opened`, and the kind `--sub-issue` takes. **`finding`**: a review finding outside the ticket, which the closing pass routes. **`contract`**: a baseline the ticket was told to follow does not hold — **the contract does not fit** — so it goes back to whoever wrote the spec or the baseline. **`deferred`**: a merely convenient change outside `## Owns`, left for a later ticket. **`decision`**: a choice only a person can make, the worker carrying on with the default; it is the child an `ABANDON: AC<n> decision` points at. **`fault`**: the pipeline itself is broken — a script, a hook, the driver, the target contract — and the agent that opens it stops. A reviewer and a verifier open no `fault`: the worker that started them is asleep until their result lands, and a `child.opened` wakes only the main agent, so each reports the failure through its own result instead. The relay wakes the main agent on a `fault` or a `decision`. In the closing pass and `NIGHT SUMMARY`, a bare *finding* means a `finding` child.
_Avoid_: `review`, `baseline`, `outside-owns`, `pipeline` (as kind names), sub-issue kind
_Home_: `mmw-v2/skills/verify-ticket/references/sub-issues.md`

**`ticket.checked`**:
One run of a ticket's criteria, or of the repository's `checks`, on one commit. Its `run` says whose: `self` for the worker's `verify-ticket.py <n>`; `reverify` for `--reverify` — the verifier's, or the main agent's on the base branch with `--actor main`, which names the main agent as the writer; `repo-checks` for the `checks` `--closeout` runs. The payload carries the full `commit`, the `result` (`met`, `unmet` or `handoff`), the counts, each criterion's outcome and evidence, the ids left unmet in `failed`, a fingerprint of the criteria it ran, on a `self` run the files under `Outside Owns:`, on a `repo-checks` run each failed command, and the product `slot` and its port base when the run held one. The comment's first line names the run and the commit and repeats gate-check's summary line, and the ledger follows, both for a person. Every reader takes the run from the event: the next run carries the newest `self` or `reverify` ledger forward, `status`'s `ac` column counts the newest, `--verdict` judges the newest `reverify` and refuses one on a commit other than `HEAD`, `--closeout` checks an `ALL MET` draft against the newest `reverify` alone — a `self` run is the party being judged reporting on itself — and `dispatch.sh reverify` counts a ticket red only on a `reverify` of `HEAD` that is not `met`. A run whose event could not be written exits 4 and counts as a run that did not happen.
_Avoid_: `self-run`, `reverify` (as the name of a comment), 自跑, 复验, `CHECKS FAILED`, `CHECKS OK`
_Home_: `mmw-v2/skills/verify-ticket/references/running-criteria.md`

**`worker.touched`**:
The event `--touched` posts on each open ticket under the same spec whose `## Owns` covers a file the worker's newest `self` run lists under `Outside Owns:`: `by` names the ticket that changed them and `files` the files, so the worker that owns them reads on its own ticket what another ticket did to them. Its comment gives each file with the `DECISIONS` sentence about it, the criterion that sentence names, and the Spec axis's judgement of it. It is refused on a ticket the reviewer has not reported on yet, since the review is what says whether those files should have been touched at all.
_Avoid_: `TOUCHED BY` (as a comment)
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`worker.queued`**:
The event a run of a ticket's criteria posts, once, when it needs the product and no slot is free: `reason` `product-full` (the product's `instance.max` is reached) or `machine-full` (every slot of this machine is taken), and the `run`. It is the one state in which a worker is neither dead nor done, and `status` notes it as `waiting for a product slot since <time> (<reason>, <k> of <max> held)`. The worker's own run then exits 3 at once, having run nothing, and the worker ends its turn; the relay wakes it with `#<n> worker.queued` each time an event that gives a slot back lands on a ticket of the batch, and it runs the same command again, under the same event while every slot is still held. A reverify waits inside the command instead, asking again every `MMW_SLOT_BEAT_S` seconds (10) and exiting 3 after `MMW_SLOT_WAIT_S` (90). The wait ends at the next `ticket.checked`, or at an event that ends the worker's hold.
_Avoid_: held (for this; see **held**), blocked (for this), queued ticket
_Home_: `mmw-v2/skills/verify-ticket/references/running-criteria.md`

**`verifier.passed`, `verifier.failed`**:
The verifier's verdict, posted by `verify-ticket.py <n> --verdict "<one line>" --model <model>` after its `--reverify` run, first line `VERDICT <full 40-character commit> by <model> — <one line>`; the script reads the commit off `HEAD`. Which of the two it is comes from the newest `reverify` `ticket.checked`, which must be a run of `HEAD` — result `met` is a pass, anything else a failure naming the criteria it left unmet in `failed` — and never from the words of the line; a line opening `could not start` is a `verifier.failed` whose criteria never ran (`ran` false). The one line says, in order, how it ran (`commands only`, or `could not start` when a criterion could not be run at all — the verifier never starts the product by hand), what came back, and what it repaired. It is bound to one commit, so the branch is merged and never rebased; it covers that commit and no later one, which is why the verifier is the last of the closing steps. An `ALL MET` draft needs one on the ticket **and** needs its commit to be `HEAD`: what was verified independently is what gets merged, and there is no line a worker can write instead — a `VERDICT` typed with `gh issue comment` carries no event and is no verdict. `HANDOFF REQUIRED` is held to none of its conditions. The verifier's whole report is this line plus the two `git status --porcelain --untracked-files=no` outputs.
_Admitted_: verdict
_Avoid_: the verdict line, verdict comment, 判决, VERDICT (as a name; it is the event's first line)
_Home_: `mmw-v2/skills/verdict/SKILL.md`

**`worker.decided`**:
The event `--decisions <file>` posts on the ticket once, after the review and before starting the verifier: first line `DECISIONS`, then `Decisions I made on my own` — every line so far, in the closing comment's shape — and `Outside Owns` — the `Outside Owns:` line of the newest `ticket.checked` of run `self`, with one sentence per file saying why. Those two sections and no others; a file whose line does not match that run, a missing or extra section, and a second run on a ticket that already carries the comment are each refused and post nothing. The Spec axis reads it and judges every line; a fix round after the verifier adds no second one, and the closing comment carries the final version. `--closeout` does not check it.
_Admitted_: `DECISIONS` comment
_Avoid_: decisions comment, 临时决策评论
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**review comment**:
The reviewer's report on the ticket, the comment the **`reviewer.reported`** event carries. Its shape: first line `REVIEW <base commit>..<HEAD commit>`, the refs as given, even when one does not resolve or the diff is empty; then the three axis reports under `## Standards`, `## Spec`, `## Tests`, never merged or reordered across axes; then `## In-ticket` and `## Out-of-ticket`; then one summary line per axis. The worker, which ended its turn after starting the reviewer, is woken with `#<n> reviewer.reported` once it lands, reads the comment off the ticket, and acks the wake.
_Avoid_: review report comment, REVIEW 评论, report (bare)
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**closing comment**:
The comment a worker leaves on handing over, written first as a **draft** file that `--closeout <draft>` checks and posts. Its fixed parts, in order: the first line `ALL MET` or `HANDOFF REQUIRED: <abandoned> abandoned (<kinds>), <unmet> unmet, <met> met of <total>`; `Branch: … Commit: … PR: none — will be merged into <base branch> by dispatch.sh advance`, where `<base branch>` is the newest `worker.started.into`; four lines per criterion, with `ABANDON:` where given; `Outside Owns:` (each file followed by the Spec axis's judgement, `reasonable` or `should not`); `skipped: [X], add when [Y]` (what was deliberately not built and the condition to build it); `Sub-issues opened:` (this ticket's sub-issues); `Counts: <met> met, <unmet> unmet, <abandoned> abandoned of <total>` (recounted at the Audit, agreeing with the first line); `Decisions I made on my own` (one line per thing the worker settled that neither ticket nor spec decides). It carries no line about the commits made after the verdict: a worker's own account of its own commits settled nothing, so the only way past a stale verdict is another verifier run. `--closeout` posts it as `ticket.passed` when its first line is `ALL MET` and as `ticket.returned` otherwise, and that event, never the line, decides whether `advance` merges the exact commit and origin base branch it names. The draft is written by `verify-ticket.py <n> --draft`, which leaves `skipped:` and `Decisions I made on my own` as `<fill>`, so its `ALL MET` is not evidence until `--closeout` accepts it.
_Avoid_: 收尾评论, handoff comment, 收尾评论草稿, 草稿 (as a term), 本票我自己拿的主意, `Post-verdict:` (the line the skeleton stopped asking for)
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`ALL MET`**:
The closing comment's first line when every criterion is met: `--closeout` refuses it when any `ABANDON:` is `failed` or `stuck`, and posts an accepted one as `ticket.passed`, the event `advance` merges on. Also the opening of one gate-check summary line shape, `ALL MET (<n> met…)`, which the first line of a `ticket.checked` comment repeats for a person; `--closeout`, `--verdict` and `status.py` read that event's `result` and counts instead.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`HANDOFF REQUIRED`**:
The closing comment's other first line, `HANDOFF REQUIRED: <abandoned> abandoned (<kinds>), <unmet> unmet, <met> met of <total>` — the way out of anything the worker cannot fix itself, held to none of the verdict's conditions. `--closeout` posts it as `ticket.returned`, swaps `ready-for-agent` for `needs-triage` and takes the claim off in one edit, leaves the ticket open, gives the product slot its worktree holds back before the event, and runs none of the repository's `checks`. gate-check's summary line has a same-prefixed shape, `HANDOFF REQUIRED: <n> abandoned (met: …)`.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`Outside Owns:`**:
The files this ticket's own commits changed that no `## Owns` glob covers, along the first-parent chain since the base commit, merges excluded: listed by the worker's `self` run in its `ticket.checked` event, whose comment ends with them as an `Outside Owns:` line, and a fixed line of the closing comment, copied into the draft and explained there with the Spec axis's judgement of each file (`reasonable` or `should not`); `None` when empty. The `worker.decided` event's comment carries the same line with one sentence per file, the Spec axis judges each, and `--touched` posts a `worker.touched` event on every open ticket under the same spec whose `## Owns` covers one of the files. `--closeout` checks none of this. The question is asked of this ticket's own commits, so a run on any branch but `issue-<n>` writes `Outside Owns: not checked on <branch>, which carries more than this ticket` instead. It is an explanation, not a criterion.
_Home_: `mmw-v2/skills/verify-ticket/references/running-criteria.md`

**question gate**:
`hook.py question <host>`: the refusal of the host's question tool (`AskUserQuestion` on Claude Code, `request_user_input` on Codex, `ask_user_question` on Grok and on Pi, `AskQuestion` on Cursor) in any session whose working directory's basename is `issue-<n>` — the ticket worktree every runner starts a worker, reviewer or verifier in, with nobody at its screen. It asks no runner. Its reason names the two ways out — take the likeliest option and record it under `Decisions I made on my own`, or `ABANDON: AC<n> decision` with `--sub-issue decision` under the ticket — so no question from a gated session reaches a screen nobody watches.
_Avoid_: form, 提问表单, BLOCKED:, MMW_AUTONOMOUS
_Home_: `mmw-v2/skills/drive-target/scripts/hook.py`

**`NIGHT SUMMARY`**:
The `spec.closed` event `dispatch.sh summary <spec>` posts on the spec when the night is over, first line `NIGHT SUMMARY <date>`, then six lines: `Closed:`, `Handed back to needs-triage:`, `Bounced:` (each `ticket.bounced` ticket and its reason), `Not dispatched, a blocker stayed open:`, `Sub-issues opened tonight:` (by number and title) and `Findings routed:` (`opened/fixed/became/skipped/unread/open`, counting the `finding` kind alone). If `reverify` ran in this checkout, a `Reverify: <green>/<red>` line is appended.
_Avoid_: 夜间总结, the night summary
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**`spec.merged`**:
The event `dispatch.sh finish <spec>` posts on the spec only after the accepted base branch has been merged into and pushed to the project branch. Its payload names `into`, `project`, the pushed merge commit in `merge`, and that merge's first parent in `base`; its first line links the compare from `base` to `merge` and the merge commit. Once present it is the durable precondition for retrying only the remaining cleanup, never for making another merge.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

### Running the criteria

**ledger**:
The temporary file `AC.md` that `verify-ticket.py` writes from `## Acceptance criteria` alone — verbatim but for the `TIMEOUT:` lines, which are this script's and are kept out of it, and, on a reverify, with the ticks and evidence of the newest `self` or `reverify` `ticket.checked` carried forward when that run ran the criteria the body states now — and hands to gate-check, the only format gate-check accepts. It cites criteria by `AC<n>` number and is deleted after use; the ledger as the run left it goes back on the ticket in that run's `ticket.checked`. gate-check's own `OWNS:` line belongs to unlazy's leases and is never written here.
_Avoid_: 账本, 临时账本, AC.md (as a name), throwaway ledger
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**gate-check**:
The judging program copied from unlazy: it walks the ledger, runs each `CHECK:` one at a time in its own shell, applies both conditions, writes `EVIDENCE:`, prints one **status line** per criterion (`RUN`, `PASS`, `FAIL`) and one **gate-check summary line** at the end — `ALL MET (<n> met…)`, `UNMET: <n> (met: <m>)`, or `HANDOFF REQUIRED: <n> abandoned (met: …)` — which the first line of every criteria run's `ticket.checked` comment repeats for a person. `gate-check.mjs` names the file. Its `--claim`, `--release`, `--scope` and `GATES.md` are unlazy features this pipeline does not use.
_Avoid_: the judging engine, gate checker, the checker (for this), 汇总行
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`

**gate-lint**:
The criterion linter copied from unlazy: it reports problems in how criteria are written and runs no command; `manual-gate` is an error here. It prints `LINT OK` or `LINT FINDINGS`. `--lint` runs it.
_Avoid_: the linter (for this)
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-lint.mjs`

### Code review

**code review**:
One round: the worker starts the reviewer with `dispatch.sh start <n> reviewer`; the dispatcher starts three general-purpose subagents, each prompted to use the `code-review` skill with a ticket, a base commit, and one axis name — Standards, Spec, or Tests — each reading `git diff <base-commit>...HEAD`; one review comment results. The round ends only with that comment: the worker ends its turn after `start`, is woken by the relay with `#<n> reviewer.reported` once the comment lands, reads the report off the ticket, and acks the wake; nothing is polled. The dispatcher holds its own turn until all three axes have answered, so that a session coming to rest means the report exists. Start exits 2: nothing was started — it is a pipeline fault: `<engine> <n> --sub-issue fault <file>`, then stop. A reviewer that stopped before its report landed is the watchdog's to find: it writes `reviewer.lost`, the relay wakes the worker with it, and the worker starts another reviewer and acks that wake. An in-ticket finding gets one round of fixes and a run of the worker's own (`<engine> <n>`), never a re-review; an out-of-ticket finding is `--sub-issue finding`. Fixing a finding is bound by the writing rules.
_Avoid_: the review stage
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**axis**:
One of the three dimensions of a code review, each a host general-purpose subagent that re-enters the `code-review` skill through the matching axis door. **Standards axis** (`Standards reviewer`): does the change follow this repository's documented coding standards, and does the same outcome exist with less code — from the documented standards, the **smell baseline** (the twelve Fowler smells, carried in full inside the reference file and never pasted into a prompt), and `codebase-design/SKILL.md`; it asks of every hunk whether it could be less, runs the deletion test on every module the diff adds or reshapes, and marks a finding `judgement call` or `hard violation`. **Spec axis** (`Spec reviewer`): does the change match what the ticket or the spec asked for, reading the baselines under `## Read first` and never the handoff package, and reading the tickets already merged into the base branch alongside it; findings are `Missing`, `Scope creep`, or `Built wrong`; it also judges every line of the ticket's `DECISIONS` comment `reasonable` or `should not`, and a `should not` is an in-ticket finding. **Tests axis** (`Tests reviewer`): are the test cases the criteria name worth trusting — its in-ticket scope is the test files and cases a `CHECK:` names, any other test file in the diff is out-of-ticket, from the **test smell baseline** copied from `tdd/tests.md` and `tdd/mocking.md`; it reports no coverage and adds no criteria the ticket lacks.
_Avoid_: 轴 (for this), Standards 轴, Spec 轴, Tests 轴, 缺项, 实现得不对, baseline smell, smell list
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**review finding**:
One item an axis subagent reports, quoting the requirement line it fails. It is **in-ticket** when it touches this ticket's acceptance criteria, a decision in the spec section the ticket names, a baseline under `## Read first`, the spec's `## Out of Scope`, the spec's `## Testing Decisions`, or a file inside this ticket's `## Owns` — then it gets one round of fixes, and `ABANDON: AC<n> failed` if the fix cannot be made; otherwise it is **out-of-ticket** and becomes a non-blocking `finding` child under the ticket (`--sub-issue finding`), labelled `needs-triage` and `mmw:child`, while the ticket still closes. The sixth condition sorts a finding onto the fix round; it does not widen where the worker may write. The dispatcher sorts them.
_Avoid_: 票内, 票外, 票内发现, 票外发现
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**reference file**:
A document under a skill's `references/` directory, reached by a relative link from its `SKILL.md`. For code review the session's steps live in `references/session.md` and each axis has its own file; an axis subagent is told the skill and the axis name, never a path.
_Avoid_: reference (bare), 判据 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

### Claiming and handing back

**preflight**:
`verify-ticket.py <n> --preflight`, the worker's first step: six checks, in order — on the ticket branch, no uncommitted tracked changes, ticket state `OPEN`, labelled `ready-for-agent`, no blocker still holding it (one that is open, one closed with a pass that has not landed, and one whose own events cannot be read all hold), no assignee but this pipeline's own account — then the claim and its `ticket.claimed` event, printing `READY: #<n> claimed on issue-<n>`. Any failure posts `ticket.refused` with the first refusal's reason, prints its `NOT_READY: …` sentence and exits 2. The checks are all in the script; the model does not perform them one by one.
_Admitted_: start-of-work guard
_Avoid_: 开工守卫, 开工核对, the guard (for this)
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**claim**:
Setting the ticket's assignee to oneself, `gh issue edit <n> --add-assignee @me`: the first write action after preflight's checks pass, and the session's first write, followed by a `ticket.claimed` event that begins the ticket's hold. A claim exists only on the tracker, and the frontier takes unassigned tickets only, which is what keeps a second worker off a ticket somebody is already working. Six paths take a claim off: the closeout, the hand back to triage, `land`, `advance`'s **give a claim back** (the `RELEASE` line) for a claim whose worker is gone, `suspend`, which gives back every claim of the batch, and `retract`, which gives the claim back once a ticket's session is gone. A session that ends any other way — a crash, a machine restart, a workspace archived from outside this pipeline — would otherwise leave the ticket off every frontier for good, with an empty frontier as the only sign of it.
_Admitted_: give a claim back (for the third path)
_Avoid_: 认领 (as a term), assign to oneself, release (in prose, for taking a claim off; the printed literals `RELEASE <n>`, the `released` of an `advance` or `land` summary line, and `released the claim on #<n>` stay as they are)
_Home_: `docs/agents/issue-tracker.md`

**hand back**:
Swapping `ready-for-agent` for `needs-triage` and leaving the ticket open: `--closeout` does it on `HANDOFF REQUIRED`, taking the claim off in the same edit (printing `HANDED BACK: #<n> is now needs-triage and stays open`). `reverify` does a related move on a landed ticket that went red: reopen, add `needs-triage`, remove the assignee, write `ticket.regressed`. `triage` reads such a ticket from its comment trail instead of reproducing it.
_Avoid_: 交回, handed back (as a name)
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**continue**:
The word the main agent appends when it `resume`s a live worker: `resume <n> "<what you settled, then: continue>"`. The session is alive and holds everything it read and wrote, so it carries on from where it was rather than being re-prompted into the work; a worker prompted back into a ticket without its own context finds its place instead in `implement`'s resume table, from the events the ticket carries.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

### Working discipline

**narrowed reading**:
The worker's reading at start of work: the ticket in full including comments and its own open sub-issues; every `## Read first` item to its conclusion; along `## Parent`, only the `## Implementation Decisions` subsections it names plus `## Testing Decisions` and `## Out of Scope`, never the whole spec; then `CONTEXT.md`. A ticket with no `## Read first` is an older one, and the fallback is every item under the spec's `## Sources`. Code review's spec-source step reads the same way.
_Avoid_: 读法收窄, 只读指名小节
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**state the seam**:
The last step before writing code: one sentence naming which layer, which directory, and which precedent to copy, taken from `## Seam`; when the ticket has no such section, derived from `## Testing Decisions` and commented on the ticket first.
_Avoid_: 说出 Seam
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**writing rules**:
The While writing code section of `implement`, between stating the seam and `Use /tdd`: the baseline is the contract (`--sub-issue contract` when it does not fit); an interface has one code path, so no request path chooses its projection by whether a data source is present, by a query parameter, or by a build switch; every surface component's root carries the `data-screen="<mount>"` the screen contract declares for that design page; `Put no question on the screen` — take the default and record it under `Decisions I made on my own`; before changing a function, grep every caller and fix the shared place; before adding a branch or guard, name and delete the one it makes redundant; before writing a helper, look for one in the repository and `## Read first`; before adding a file, dependency, or configuration, say why the existing one is not enough; never simplify away security, data-loss prevention, accessibility, or what the ticket explicitly asks for (`## What to build`, every criterion, the baselines, the Seam interface); at the end write `skipped: [X], add when [Y]`; Owns two grades (`--sub-issue deferred` for a convenient change).
_Admitted_: While writing code
_Avoid_: 写码纪律, 写码纪律七条, the seven working rules, 不问 (as a name)
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**closing steps**:
What `implement` does once the code is written: bring in what landed on the base branch while the work ran (`<dispatch> integrate <n>`) and then the worker's own run (`<engine> <n>`); start the reviewer (`<dispatch> start <n> reviewer`), fix in-ticket findings for one round, `--sub-issue finding` for the out-of-ticket ones, no re-review; `--decisions`; start the verifier (`<dispatch> start <n> verifier`) once, since `--closeout` requires its verdict to cover `HEAD` and every earlier step still writes commits; `Audit`; `--touched`; `--sub-issue decision` for criteria that only wait for a person's one sentence, then `--draft` and fill the two placeholders; `--closeout`. `--closeout` archives no agent: landing does that, and takes the workspace with the agents inside it (`land <n>` for one ticket, `advance` for a batch). A resumed worker claims the ticket again with `--preflight` and then resumes at the step `implement`'s resume table gives for what the ticket carries — its `ticket.checked` events and its `reviewer.started`, `reviewer.reported`, `reviewer.lost`, `worker.decided`, `verifier.started`, `verifier.passed`, `verifier.failed` and `verifier.lost` events. `--closeout` pushes the ticket branch to `origin` before it closes the ticket, and no pull request is opened: work reaches the base branch through `land` or `advance`.
_Avoid_: 收尾七步, 收尾六步, the seven closing steps, the closeout (for the sequence)
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`Audit`**:
The closing step that re-reads the whole ticket and every `## Read first` item, traces every criterion to its latest `EVIDENCE:`, and recounts `Counts:`.
_Avoid_: 交接前自审
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**closeout**:
`verify-ticket.py <n> --closeout <draft>`, the closing gate — the only place in the pipeline that closes a ticket or changes its queue label while it is being worked. It checks the draft against the ticket and the repository (first line, `ABANDON:` kinds, evidence behind every tick, `Counts:` agreeing with the first line, the newest reverify `ticket.checked` with result `met`, that run covering the criteria the ticket now states, a `verifier.passed` or `verifier.failed` event whose `commit` is `HEAD`, a `Missing` the Spec axis raised against a screen-contract row the ticket owns named in the draft too, no unreadable event on the ticket, no uncommitted tracked changes, the branch containing the base commit of the newest `worker.started` and — for `ALL MET` — that event carrying an `into`, and the ticket still `OPEN` and assigned to this account). A draft that fails those conditions changes nothing, names the first condition and the count on stderr with every other opening `also:`, and exits 1; the worker fixes the draft or the ticket and runs again. After an `ALL MET` draft is accepted it runs `.mmw/target.json`'s optional `checks` and posts them as a `ticket.checked` of run `repo-checks`; an `unmet` one leaves the ticket open. Then it pushes the verdict commit to `origin/issue-<n>` without force and confirms it landed, closes the ticket (`gh issue close --reason completed`), takes `ready-for-agent` and the claim off in one edit, and only then posts the comment as `ticket.passed`, printing `CLOSED: #<n>`; on `HANDOFF REQUIRED` it hands the ticket back, leaves it open, gives back the product slot its worktree holds, if any, and then posts the comment as `ticket.returned`. The state change comes before the event either way, so an event never stands on a ticket the tracker did not change, and a run that made the change and could not post the event is finished by running it again with the same draft. It archives no agent. `--check-only` is the dry run, printing `CLOSEOUT OK: #<n> draft passes every check`, and does not run `checks`. A command that would bypass it is refused by `hook.py`.
_Admitted_: closing gate
_Avoid_: 关票门, the gate at the end, 关票 (as a term)
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**the ticket is the only state**:
Every run reads the ticket afresh, writes its events there, and carries nothing to the next run but what they say; the ledger is thrown away; the ticket body is never edited — run state lives in the comments, and where a ticket stands is their fold. `status.py` keeps no state file for the same reason. The relay's state directory holds only what the relay has to deliver — wake-up rows, acks, its marks on each ticket — and never a ticket's state.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**The environment is yours; the repository is not**:
The verifier may install a dependency, download a browser, or find a connection string, and leaves the repository exactly as it found it; two identical `git status` outputs are the proof. What it never repairs is what the machine hands out: ports and the data directory come from the lease, and the product is started and stopped only by `.mmw/target.json`'s own commands, which the criteria run themselves.
_Avoid_: the verifier's boundary
_Home_: `mmw-v2/skills/verdict/SKILL.md`

**No pull request**:
No step of the pipeline opens or reads a pull request: `--closeout` pushes `issue-<n>` to origin without force before it closes the ticket, and `land` and `advance` fetch origin and merge into the base branch `worker.started.into` names, so a pull request would only be a second merge queue nothing here reads. The closing comment's `PR:` line says `none` with that reason, and the `ticket.landed` event's compare and commit links give the whole-ticket diff and merge destination instead.
_Home_: `mmw-v2/merge-notes/implement.md`

### Values at a glance

| name | values |
| --- | --- |
| event | `spec.opened` · `spec.suspended` · `spec.closed` · `spec.merged` · `ticket.claimed` · `ticket.refused` · `ticket.passed` · `ticket.returned` · `ticket.released` · `ticket.landed` · `ticket.regressed` · `ticket.bounced` · `ticket.checked` · `worker.started` · `worker.resumed` · `worker.retracted` · `worker.replaced` · `worker.decided` · `worker.queued` · `worker.touched` · `worker.lost` · `reviewer.started` · `reviewer.reported` · `reviewer.lost` · `verifier.started` · `verifier.passed` · `verifier.failed` · `verifier.lost` · `child.opened` · `child.closed` |
| event subject | `spec` · `ticket` · `worker` · `reviewer` · `verifier` · `child` |
| common payload field | `v` · `event` · `stage` · `actor` · `spec` · `ticket` · `at` |
| ends every hold | `ticket.landed` · `ticket.returned` · `ticket.released` · `ticket.bounced` · `spec.suspended` |
| ends one session's hold | `worker.retracted` · `worker.lost` · `worker.replaced` · `reviewer.lost` · `verifier.lost` · `ticket.refused` (naming its session) |
| gives the product slot back (`SLOT_ENDS`) | `ticket.landed` · `ticket.returned` · `ticket.released` · `ticket.bounced` · `spec.suspended` · `worker.retracted` |
| `ticket.refused` reason | `wrong-branch` · `dirty-tree` · `not-open` · `not-ready` · `blocked` · `claimed-by-other` |
| `ticket.released` reason | `landed` · `suspended` · `worker-lost` |
| `ticket.bounced` reason | `conflict` · `checks` |
| `ticket.checked` run | `self` · `reverify` · `repo-checks` |
| `ticket.checked` result | `met` · `unmet` · `handoff` |
| `worker.queued` reason | `product-full` · `machine-full` |
| ends the hold of the session that produced it | `reviewer.reported` · `verifier.passed` · `verifier.failed` |
| gate-check status line | `RUN` · `PASS` · `FAIL` |
