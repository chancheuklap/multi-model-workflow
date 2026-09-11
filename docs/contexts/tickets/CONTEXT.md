# Tickets

The written half of the landing pipeline: what a spec and a ticket are, how each section of them is written, how a batch is published, read back and linted, and which labels and queues an issue carries while it waits. Every other context in this pipeline reads what this one wrote, so the wording fixed here is the wording a worker, a reviewer and a verifier find on the ticket.

How to read an entry: the bold line is the term's only name; a term whose name is a literal string that appears in a file, a command, or a comment is named by that string exactly (case, colon, and all). The definition says what the thing is and what sets it apart from its neighbours. `_Admitted_` lists the one other wording that may appear in prose. `_Avoid_` lists dead words: a sentence in this repository that uses one is wrong; an item followed by a note in parentheses says in which sense the word is dead. `_Home_` is the file whose text or code the definition is taken from; when this file and that one disagree, that one is right and this file is rewritten. An attribute that can be had by reading that file — a field list, an exit code, a command's switches, the branches of a behaviour — is not repeated here: an entry says what the term is and how it differs from its neighbours, and points at `_Home_` for the rest.

## Language

### Worker grades

**worker grade**:
Which of the two workers a ticket goes to. Each grade is at once a ticket label and a row of `models.json`; the user sees it once, as the `Worker:` line of the `to-tickets` quiz, and the label is read afresh every time the ticket is started — `dispatch.sh` reads the labels off the ticket, falls back to `DEFAULT_WORKER` when there is none, refuses a ticket carrying both, and resolves the named row against tonight's runner catalog.
_Avoid_: grade of worker, seat, lane (for this)
_Home_: `~/.mmw/models.json`

**`junior-worker`**:
The default worker grade (`DEFAULT_WORKER` in `dispatch.sh`). A ticket whose `## Seam` already names a precedent to copy stays on it.
_Avoid_: 初级工人, 初级 worker
_Home_: `~/.mmw/models.json`

**`senior-worker`**:
The worker grade a ticket names when getting it wrong would be wrong silently — money that has to reach a terminal state, recovery after a crash, a contract an installed base already reads, a security default — because none of those fail on the day they are written.
_Avoid_: 高级工人, 高级 worker
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

### Specs

**issue**:
A GitHub issue, the issue tracker's unit. In this pipeline it is a spec, a ticket, a sub-issue, a decision ticket, a map, or an issue from outside that triage handles. Its **ticket state** is `OPEN` or `CLOSED`.
_Home_: `docs/agents/issue-tracker.md`

**spec**:
A top-level issue that holds a batch of tickets. It is a container, not work, so it carries no queue label; its one label is the layer label `mmw:spec`, which `to-spec` puts on when it publishes it. `to-spec` writes it from the conversation, a cleared map, or an agent brief, in the `<spec-template>` shape: `## Problem Statement`, `## Solution`, `## User Stories`, `## Implementation Decisions`, `## Testing Decisions`, `## Out of Scope`, `## Sources`, `## Further Notes`. Decisions that share one seam belong in one spec. A worker reads only the subsections its ticket's `## Parent` names, plus `## Testing Decisions` and `## Out of Scope`. A section of a published spec is changed in place by `to-spec`'s step for revising a published spec — the body stays the clean current version, what changed and why goes in one comment — so the number and every ticket's `## Parent` stay valid. The night runs on it: `open <spec>`, `advance <spec>`.
_Admitted_: spec issue
_Avoid_: 父票, spec 票, 规格
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Implementation Decisions`**:
The spec section of decisions made, in numbered subsections `### 1.` … that tickets point at by number in `## Parent`. Every decision names its source at the end of the sentence or table row that states it — a decision ticket number, an ADR id, a research or prototype path, a screen-contract row id — or says `this spec's decision`. Whatever a story under `## User Stories` settles about a control, a value, a transition or a failure is folded into the subsection that implements it, with the story number as its source, because a worker reads these subsections and never a story. It names no implementation file paths.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Testing Decisions`**:
The spec section whose first sentence says in plain words where a test looks at the result (a browser page, an HTTP endpoint, or a function call) and whose second names the seam, what is real on each side of it, and which external seams may be stubbed; then what makes a good test; then, per test layer, its directory and the precedent to copy; then **How a test arrives at a state** — the mechanism that puts the system into each state the behaviour turns on, which must be named here and owned by some ticket's `## Owns`, else `to-tickets` cuts a `reach` ticket for it; then, where the effort has a screen contract, the **Test surfaces** that make the repository a runnable environment; last, the commands to run before committing. `CHECK:`, `EXPECT:`, and the ticket's `## Seam` are derived from it; a review finding that touches it is in-ticket.
_Avoid_: 测试怎么到达状态
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Out of Scope`**:
The spec section of what is not being done; read by the worker and the Spec axis along `## Parent`, and the sharpest source of a `Scope creep` finding, which is in-ticket. (A wayfinder map's **Out of scope** section is a different literal, carried into the spec unchanged.)
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Sources`**:
The spec section of links to the first-hand material it was built from, one line per kind in eleven fixed kinds — wayfinder map, decision tickets, Upstream specs, ADRs, research files, prototype directories, handoff package, screen contract, Domain docs, Evidence, Test rules — `none` when a kind is empty, so a reader can tell "nothing there" from "forgot to list". `## Read first` picks per ticket from here.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**seam**:
The place a test observes: the public boundary you test at. `to-spec` chooses it without asking the user, preferring an existing one and the highest one available, and asks the other half in the same breath — whether a test can put the system into every state the behaviour turns on through that seam. It is the subject of `## Testing Decisions`'s second sentence and of a ticket's `## Seam`. **External seams** are the third-party ones that may be stubbed.
_Avoid_: boundary (for a seam)
_Home_: `mmw-v2/upstream/skills/engineering/tdd/SKILL.md`

**precedent**:
The similar existing test `## Testing Decisions` names per test layer. It is copied into the ticket's `## Seam`; the ticket writer opens it to copy its framework and single-file invocation into `CHECK:` and runs it once to take the `EXPECT:` marker. A layer with no precedent yet — a project from zero — gets one from the contract ticket, whose adapter, interaction helper and journey skeleton are the precedents the tickets behind it copy; nothing about a missing precedent sends the batch back to `to-spec`.
_Admitted_: the precedent to copy
_Avoid_: prior art, 先例, the precedent it names
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**test layer**:
The layer a feature's tests land in — named per layer with its directory and precedent in `## Testing Decisions` and copied into `## Seam`. The toolbox's own tests have five layers: **structural check** (`install.sh --check`), **own-script layer** (this repository's scripts against fixed samples, entry `tests/run.sh` per skill), **vendored-script layer** (the tests that came with copied upstream scripts), **skill-behaviour layer** (run the skill for real on a throwaway ticket inside a worktree and check what appears on the ticket), and **real ticket** (one real ticket carried from writing to closing; nothing merges to the base branch until it passes).
_Avoid_: 测试层, 结构核对, 自写脚本层, vendor 脚本层, 技能行为层, 真票
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

### Tickets

**ticket**:
A GitHub issue created as a native sub-issue of its spec (`gh issue create --parent <spec>`, or attached through the `sub_issues` API), in the `<issue-template>` shape and carrying the layer label `mmw:ticket`. It is a tracer-bullet vertical slice with its blocking links; the only place fact and state are kept; the worker's only input; it must have an issue number. At publication it takes one of two shapes: an agent ticket (labelled `ready-for-agent` plus a worker grade) or the separate `ready-for-human` ticket. A ticket this repository plans for itself carries a state role only. Its **ticket body** is the sections, not edited once the batch has been reported to the user as published — the read-back step, which fixes tickets and runs `--lint` again, comes before that report; its **ticket number** is `<n>` — digits only. A **batch** is the tickets under one spec, published together and worked in one night.
_Admitted_: issue (when naming the GitHub object)
_Avoid_: 票 (as a term), child ticket, slice (as a name), 本批, 票号, body (bare)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**vertical slice**:
The rule that a ticket cuts a narrow but complete path through every layer — schema, API, UI, tests — and never a horizontal slice of one layer; a finished slice is demoable or verifiable on its own, and its title and `## What to build` describe the same slice. Prefactoring is done first. Wide refactors are the exception: one mechanical change whose effect fans across the whole codebase is not forced into a tracer bullet but sequenced — add the new form beside the old, migrate the call sites in batches, each batch its own ticket, then delete the old form in a ticket blocked by every batch.
_Admitted_: tracer-bullet
_Avoid_: 纵切, slice (as a name)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`<issue-template>`**:
The ticket template in `to-tickets/SKILL.md`: `## Parent`, `## What to build`, `## Read first`, `## Seam`, `## Owns`, `## Acceptance criteria`. Sections read by position downstream keep these exact headings; renaming one means changing `implement` too.
_Avoid_: 六节, 七节, 八节 (as names)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Parent`**:
The route from the ticket to its spec: `#<spec>, Implementation Decisions section <n>`. The section number is omitted only when the source was not an existing issue. One of the five things a `ready-for-human` ticket holds.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## What to build`**:
The end-to-end behaviour this ticket makes work, from the user's point of view, in numbered points each with the test that decides it and the reason it is there; a choice the user settled in the `to-tickets` quiz is a point of its own. It describes the same slice as the title (checked at read-back and after claiming) and is never simplified away.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Read first`**:
The sources the ticket's spec subsections cite, `None` when there are none. Each item is read to its conclusion before work: a research file's last section, an ADR's decision (its `# ` heading and the prose under it), a handoff package, a prototype's leaf README.md to its verdict. Items that record a settled conclusion are baselines and are marked as such on their line. On an interface ticket the rest of the section is derived rather than hand-picked, from the row ids this ticket owns: the baseline sources those rows cite, and the target trees of its design pages. It is re-read at the Audit, and searched before a helper is written.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**baseline**:
An item under `## Read first` that records a settled conclusion: a decision ticket's resolution, an ADR's decision (its `# ` heading and the prose under it), a research file's conclusion, a handoff package, a prototype's chosen artifact. To the worker it is a contract, not a reference; a handoff package is copied verbatim, a prototype is rewritten to production standard. The Spec axis reads the baselines against the diff, and a deviation is `Built wrong`. The screen contract's `baselines.look` names the handoff package directory, and the story judge's output word for that side is `baseline`.
_Avoid_: 基线 (as a term), reference (when this is meant), `baseline` (as a child kind; a baseline that does not hold is a `contract` child)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**contract**:
The bond between a worker and every baseline in `## Read first`, in three clauses: copy exact values, wording, states, and interface shapes; never deviate quietly; never bend a baseline, a harness, or a test. **The baseline is the contract** is the first of the writing rules. An interface ticket has two baselines, each binding its own domain — the handoff package look and verbatim copy, the screen contract what a control calls, which field feeds each shown value, what state follows, what failure shows and timing — so the two never compete. **The contract does not fit** is the case where a baseline lacks a state, a field, an interaction, or a case the work needs, or two baselines conflict on the same domain: keep going, open a `contract` child under the ticket (`--sub-issue contract`), add nothing quietly; a screen-contract row that does not fit names the alignment ticket in the child.
_Avoid_: 契约 (as a term), 安装契约, 接口契约, 基线是契约, 契约装不下, 基线装不下
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`## Seam`**:
Where this ticket is verified: the test layer and directory copied from `## Testing Decisions`, the precedent to copy, and how a test arrives at the state. Present and non-empty on every agent ticket; when a ticket lacks it, the worker derives it from `## Testing Decisions` and comments it on the ticket before writing code.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Owns`**:
The repository-relative paths this ticket may write, one per line — where you may write, not where the code is. It includes the Seam's test directory or file; a path the ticket creates is marked `(new)`; no absolute path, `..`, or bare `**`; everything outside is read-only for this ticket. Two tickets on one frontier may not overlap; where they would, a blocking link is added on the tracker. A ticket that has a directory to itself writes a **directory glob**; several tickets dividing one directory go down to file level. The **Owns check** at start of work confirms every glob matches or is `(new)` (an older ticket derives one from its Seam and the spec sections `## Parent` names, and comments the derived list on the ticket). A ticket that deletes or renames a public name — a file, a script, a contract field, a criterion word — takes every `grep` hit for that name into its own Owns, or opens a cleanup ticket `Blocked by` the ticket that owns a stale reference. The **Owns two grades** rule handles a file outside Owns: change it and record it under `Outside Owns:` when a criterion cannot pass otherwise; leave it and open a `deferred` child (`--sub-issue deferred`) when the change is merely convenient.
_Avoid_: 目录 glob, Owns 核对, Owns 两档
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Acceptance criteria`**:
The ticket section holding the acceptance criteria, one after another. A `ready-for-human` ticket has none.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**Blocked by**:
One of the five things a `ready-for-human` ticket holds: the ticket that produces the thing it waits on. An agent ticket carries no such item; its blocking lives on the tracker's native blocking links alone.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

### Acceptance criteria

**acceptance criterion**:
One standard on a ticket, decided by one command — a judgement that is not decided by a command is not an acceptance criterion. Four lines: `- [ ] AC<n>:`, `CHECK:`, `EXPECT:`, `EVIDENCE: pending`, with `CWD:` and `TIMEOUT:` as the two optional attribute lines. Three writing rules: externally observable behaviour, exact values copied from the spec or a prototype artifact, one assertion each. Numbered when the ticket is written and never renumbered, because the ledger cites by number; one whose premise later disappears is taken out of the section rather than left there without a command, its number is not reused, and the closing comment says what became of it. `--lint` checks how it is written, `verify-ticket.py <n>` runs it, the verifier re-runs it; a reviewer may not add criteria the ticket lacks.
_Admitted_: criterion
_Avoid_: AC (in prose), 标准 (as a term), 验收标准, gate (for a criterion), oracle, 判据 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`CHECK:`**:
The shell command that decides a criterion. It runs in its own shell with the working directory at the repository root (or `CWD:`); a multi-line command is written only as a fenced block directly under it. It is the one line in the pipeline a shell runs with no agent in between, so the program that runs it supplies its environment: `verify-ticket.py` sets `MMW_TICKET` to the ticket number and puts the directories in force on that shell's `PATH` — the `drive-target` skill's `scripts/`, resolved from the running script's own location, or the `--tools` directories instead — and the line names a judge by its bare name and carries no install location. A run whose ticket names a judge that neither those directories nor `PATH` holds is refused before anything starts. Its text comes from the precedent named in `## Testing Decisions`. A command may write `$MMW_TICKET` for the ticket number it is running against.
_Avoid_: check command, the check (for this)
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**`EXPECT:`**:
The string, or `/…/flags` regex, the `CHECK:` output must contain. It is written to the **success-only marker** rule: the line the precedent prints only when it passed, copied whole after running it once — never `ok`, `passed`, or `done` on its own. `gate-lint` reports a weak one as `weak-expect`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`EVIDENCE:`**:
The fourth line: `pending` until the criterion has run, then the one line of fact gate-check writes (the **EVIDENCE structured line**). A pass is written `exit=0; shell=…; cwd=…; path=…; EXPECT=matched; output-sha256=…; output-bytes=…`; a failure is written in the same fields with its own exit code (and `signal=` or `error=` where there is one), `EXPECT=not matched` where it did not match, and a trailing `output=` summary, so a red that does not repeat can still be explained. The checkbox stays the authority: a ticked criterion still reading `pending` is unmet, and evidence on an unticked line does not make it met.
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs`

**`CWD:`**:
The optional attribute line naming the working directory `CHECK:` runs in. gate-check calls the indented lines under a criterion its **attributes** and recognises four names in all — `CHECK:`, `EXPECT:`, `EVIDENCE:`, `CWD:`; one written flush left is a parse error naming the indent.
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/lib/gates.mjs`

**`TIMEOUT:`**:
The optional attribute line `TIMEOUT: <seconds>` under a criterion: how long its `CHECK:` may run. `verify-ticket.py` reads every `TIMEOUT:` off the ticket body on every run, worker's and verifier's alike, and hands gate-check the largest of `DEFAULT_TIMEOUT` (600), those lines, and `--timeout`; it raises the limit and never lowers it, and is kept out of the ledger. `--lint` reports one that is not a positive whole number as `ERROR … [bad-timeout]`.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**fenced block**:
The only way to write a multi-line `CHECK:`: a code fence directly under it is the command; every other fence in the ticket is skipped; a flush-left continuation line with no fence is a parse error.
_Avoid_: fenced check, fenced code block, 代码块围栏, 围栏
_Home_: `mmw-v2/skills/verify-ticket/references/running-criteria.md`

**the five questions**:
What the ticket writer asks, in order, of anything there is to say about the work, stopping at the first yes: is it a comparison a machine can reach, and so an acceptance criterion? a judgement a machine can reach, and so a code-review judgement (written into the spec's `## Implementation Decisions` subsection the ticket names, where the Spec axis reads it as in-ticket)? a person's reaction, and so a `reaction` ticket? something a machine could decide if it could reach the thing — which stays a criterion when the mechanism that reaches the state is named under **How a test arrives at a state** and owned by some ticket's `## Owns`, and becomes a `reach` ticket when it is not? or a choice — asked of the user in the quiz, the answer written into the ticket's `## What to build`.
_Avoid_: 五问, 五问判定树
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**both conditions**:
What it means for a criterion to pass: the `CHECK:` exits 0 and its output matches `EXPECT:`. gate-check applies it, and the rule is upstream's, unedited here.
_Avoid_: 双条件, the double condition
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`

**`met`, `unmet`, `abandoned`**:
The three states of a criterion: **met** is ticked with real evidence; **unmet** is not ticked, or ticked with `EVIDENCE: pending`; **abandoned** carries an `ABANDON:` line. **ticked** is the checkbox state in the ledger; `--reverify` re-runs ticked criteria too. A criterion is **runnable** when both `CHECK:` and `EXPECT:` are non-blank.
_Avoid_: 勾 (as a term)
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**round**:
One fix-and-rerun pass on one criterion. How many a criterion gets is the worker's judgement — keep fixing while a fix is in sight — and no run names a limit: `--closeout` counts none, so the reason on the `ABANDON:` line is the whole record of what was tried. Code review gets exactly one round, its in-ticket findings fixed once and no re-review; the verifier gets exactly one, and a `verifier.failed` ends in `HANDOFF REQUIRED` rather than a second verifier.
_Avoid_: 轮 (as a term), 三轮上限
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`ABANDON:`**:
The line `ABANDON: AC<n> <kind> <reason>` a worker — never the verifier — writes under a criterion it gives up on. The kinds: **`failed`** — it ran and did not pass (after the rounds the worker judged worth spending, or still failing after the review fix or the verifier's report), its reason saying what each round tried; **`stuck`** — it will not start or cannot be done within the ticket (a `CHECK:` that will not run, a missing credential or device, still broken after the verifier repaired its environment), its reason listing the routes tried or pointing at the sub-issue; neither is held to a round count, giving up on the first round is allowed for both, and the two are told apart for whoever reads the ticket in the morning; **`decision`** — both options are legal and neither the ticket nor the spec says, so the line carries the question, the options and the default when nobody answers, a `decision` child is opened under the ticket (`--sub-issue decision`), and it is the only kind that still lets the ticket close `ALL MET`. A UI difference never goes here. `failed` and `stuck` force `HANDOFF REQUIRED`.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

### The graph

**blocking link**:
The tracker's native dependency edge, the copy every script reads. A **blocker** is a ticket that must land before this one is dispatched, unless it closed without a `ticket.passed` and so lets go on closing; `--preflight` refuses while it holds — open, passed and not landed, or closed with events that cannot be read (`events.py` `blocker_hold`). `--lint`'s ticket graph and the night's frontier are computed from it; GitHub's `issue_dependencies_summary.blocked_by` counts open blockers only. Adding one takes the blocker's **database id** (`gh api … --jq .id`). A blocker under another spec is reported as `cross-batch`.
_Admitted_: native issue dependencies (when naming the GitHub feature)
_Avoid_: blocking edge, dependency (for this), edge (for this), native blocking link, 上游票号, blocking ticket
_Home_: `docs/agents/issue-tracker.md`

**frontier**:
The tickets `advance` may start right now, in ticket order: `OPEN`, labelled `ready-for-agent`, no unreadable event, every blocker landed, no assignee, not held. A blocker that closed without a `ticket.passed` lets go on closing, since nothing of it will ever land. All of it is read off the tracker and no runner is asked. `status.py --advance-plan` lists them; the main agent starts them with `advance`. `## Owns` must not overlap on one frontier. Wayfinder's frontier query (open, unblocked, unclaimed children of a map) is a different set.
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**assignee**:
The ticket field `claim` sets. It is one of `--preflight`'s six checks; a frontier ticket has none; hand back removes it.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**sub-issue**:
The tracker's native parent–child relation, in two levels under a spec. A spec's direct children are the batch: every ticket is created under its spec, and `--lint`'s ticket graph and the night's frontier read them, with each ticket's children, in the one GraphQL query of **`tree.py`**; a spec with none is the lint `ERROR` `[no-sub-issues]`. A ticket's direct children are the pending items it produced: an issue a worker opens under the ticket with `--sub-issue <kind>`, labelled `needs-triage` and `mmw:child`, of one of the five **child kinds**; recorded on the ticket as a `child.opened` event, which is where the ticket's fold counts its children, and listed on the closing comment's `Sub-issues opened:` line. A `finding` routed `became-ticket` in place leaves that level: its parent moves to the spec and it is a ticket of the batch. Only a spec's direct children are dispatched by `advance` or drawn into `--lint`'s ticket graph. A wayfinder map's child tickets are its sub-issues too.
_Admitted_: child (in the wayfinder map's context); children, direct children (the two-level invariant)
_Avoid_: sub_issues (in prose), child ticket
_Home_: `mmw-v2/skills/verify-ticket/references/sub-issues.md`

### Labels and queues

**label**:
A GitHub label on an issue, from one of three sets that each answer one question and never stand in for each other: a **layer label** says which layer of the tree the issue is, a triage label which queue it is in, a worker-grade label which worker row starts it. `wayfinder:*` are the wayfinder skill's own, and `bug` and `enhancement` belong only to issues from outside. A spec carries its layer label and no other. On a ticket in the agent queue only `--closeout` changes a queue label; the hook refuses a worker's `gh issue close` on that ticket and any `gh issue edit` on it that removes `ready-for-agent` or adds `needs-triage` or `ready-for-human`.
_Avoid_: 标签 (as a term), label string (as a term)
_Home_: `docs/agents/issue-tracker.md`

**layer label**:
One of `mmw:map`, `mmw:spec`, `mmw:ticket`, `mmw:child`: which of the four layers of the tree an issue is — a wayfinder map, a spec, a ticket, a ticket's child — so a board reads the layer off a label rather than counting how deep the issue is nested. It puts an issue in no queue, and no script takes a ticket's spec from it: a ticket's spec is its direct parent. The wayfinder skill puts `mmw:map` on the map, `to-spec` `mmw:spec` on a spec, `to-tickets` `mmw:ticket` on each ticket, `--sub-issue` `mmw:child` on each child, and a `became-ticket` **route** turns a finding's `mmw:child` into `mmw:ticket`; whichever comes first in a repository creates the label, with the colour and description `docs/agents/issue-tracker.md` gives.
_Avoid_: layer (bare, for the label), level label, depth label
_Home_: `docs/agents/issue-tracker.md`

**queue**:
What a label expresses and nothing more. `ready-for-agent` is the **agent queue** (waiting to be dispatched or being worked; the assignee says which); `needs-triage` is the queue of what nobody has judged, the only one a skill fetches from on its own; `ready-for-human` is the user's queue, its tickets naming `reaction` or `reach`. A queue holds one shape of ticket. Only `--closeout` moves a ticket out of the agent queue.
_Avoid_: 队列, agent lane
_Home_: `docs/agents/triage-labels.md`

**triage role**:
A canonical name the skills use; `docs/agents/triage-labels.md` maps each to the label string this repository uses, which is the same string. Five **state roles** and two **category roles**; an issue from outside carries one of each, a ticket this repository plans for itself a state role only.
_Avoid_: 角色 (bare)
_Home_: `docs/agents/triage-labels.md`

**`needs-triage`**:
Nobody has judged it yet: an issue from outside, a ticket its worker closed out as `HANDOFF REQUIRED`, or a closed ticket reopened after the night because a criterion failed on the base branch (label added, assignee removed, the failing `AC<n>` and the base-branch commit in its `ticket.regressed` event). `triage` reads this queue and recommends one of the four outcomes. A child a worker opens carries it beside `mmw:child`, under its ticket, until a `became-ticket` route makes it a ticket under the spec.
_Home_: `docs/agents/triage-labels.md`

**`needs-info`**:
Waiting on the user for more information; one of the four outcomes; serves only work from outside.
_Home_: `docs/agents/triage-labels.md`

**`ready-for-agent`**:
The agent queue. `to-tickets` puts it on every agent ticket beside the worker-grade label; it is one of the five frontier conditions and `--preflight`'s fourth check; without it `dispatch.sh` prints `REFUSE`; it comes off at both exits of `--closeout`; it never goes on a spec.
_Home_: `docs/agents/triage-labels.md`

**`ready-for-human`**:
One thing only a person can do, of kind `reaction` or `reach`. It is a separate ticket of a different shape holding **the five things** only — `## Parent`, which kind, What to look at (a link that opens, not a command), What makes it right, `## Blocked by` (the ticket that produces the thing) — with no Seam, Owns, criteria, or worker-grade label. Three writers (`to-tickets`, `triage`, code review's sub-issue path) and no automatic reader; the morning's second query lists it.
_Avoid_: 五样, Requires human implementation
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`reaction`**:
The `ready-for-human` kind where the property asserted is a person's reaction: the person is the measuring instrument, not a fallback judge, because the agent is not who is being measured, and the ticket cannot be retired.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`reach`**:
The `ready-for-human` kind where a machine would decide it if it could get to the thing — a device, a credential, a real environment, a mechanism under **How a test arrives at a state** that has no name or no owner in `## Owns`, or a consuming repository's testability rule that gives a test no exit; the ticket adds one line naming what would retire it. A pile of `reach` tickets says the pipeline lacks a capability.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`wontfix`**:
Will not be done; one of the four outcomes; serves only work from outside. The issue is closed with a comment that depends on why, and a rejection may be recorded in `.out-of-scope/`.
_Home_: `docs/agents/triage-labels.md`

**`bug`, `enhancement`**:
The two category roles, exactly one on every triaged issue from outside; never on a spec's tickets.
_Home_: `docs/agents/triage-labels.md`

**decision ticket**:
A child issue of a `wayfinder:map` holding one question whose **resolution** is a decision: a resolution comment, the issue closed, a context pointer (gist plus link) appended to the map's Decisions so far. Its resolution comment is a baseline source. It carries a state role and no category role; `AFK` and `HITL` say whether the agent works it alone. Its type label is `wayfinder:<type>` — research, prototype, grilling, task.
_Avoid_: wayfinder ticket
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**map**:
Wayfinder's single issue labelled `wayfinder:map` and the layer label `mmw:map`, the canonical index: Destination, Notes, Decisions so far, Not yet specified (the fog), Out of scope, `## Specs`. Its children are decision tickets; it is cleared when the frontier and Not yet specified are both empty, and never closed. One of the eleven `## Sources` kinds.
_Admitted_: wayfinder map (in `## Sources`)
_Avoid_: shared map (in this repository's text), 地图 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**agent brief**:
The record `triage` posts on an issue or PR at the evaluation stage — an investigation record, not a work order, and nothing is dispatched from it — ending with the disclaimer line `*This was generated by AI during triage.*`. `to-spec` reads it as one of the spec's sources.
_Avoid_: brief (bare), 工单
_Home_: `mmw-v2/upstream/skills/engineering/triage/AGENT-BRIEF.md`

### Publishing, linting, and the queues in the morning

**publish**:
Creating the spec or the tickets as GitHub issues (`publish to the issue tracker`): each ticket as a native sub-issue of its spec in dependency order, labelled `mmw:ticket` plus `ready-for-agent` and a worker grade, or `ready-for-human`. The **read-back** step follows: every ticket is fetched again — title and `## What to build` describe one slice, the spec's sub-issue count equals the batch and every one carries `mmw:ticket`, `## Read first`, `## Seam` and `## Owns` are present and non-empty, no two tickets on one frontier overlap in `## Owns`, every mechanism under **How a test arrives at a state** is owned — and every ticket with criteria is run through `--lint`, its `ERROR`s fixed and its `WARN`s read. The `ready-for-human` ones are checked for all five things. What fails is fixed before the batch is reported as published.
_Avoid_: 发布 (as a term), 出票 (as a term), 回读 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**lint**:
`verify-ticket.py <n> --lint`: gate-lint, plus the ticket graph (`cycle`, dangling references, `cross-batch`), plus the worker-label check, plus the screen-contract checks. Given the spec instead of a ticket — an issue with no `## Acceptance criteria`, no parent, and sub-issues — it checks every sub-issue the same way, closed ones included, then the graph once, and ends with the list of tickets that had an `ERROR`. Every finding carries a problem tag and a level, `ERROR` or `WARN`; only `ERROR` affects the exit code. When the graph has no cycle and no dangling reference it prints the **start levels** — the order tickets may be started in, built from this spec's own blocking links. A batch converges when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose. It is run at the read-back step, and again before a night's first `advance`.
_Avoid_: 票图核对, the linter (for this), 启动层级
_Home_: `mmw-v2/skills/verify-ticket/references/linting.md`

**problem tag**:
The label a lint finding carries: from gate-lint `parse`, `tautological-check`, `weak-expect`, `path-read-as-regex`, `manual-gate`, `unmeasured-number`, `activity-not-outcome`, `mostly-manual`; from `verify-ticket.py` `dollar-without-m` (`ERROR`), `bad-timeout` (`ERROR`), `shared-state`, `cross-batch`, `cycle`, `duplicate-ticket`, `blocker-not-a-ticket`, `no-sub-issues`, `worker-label` (`ERROR`: no worker-grade label, or both), `screen-contract` (`ERROR`: an interface ticket naming no contract rows, a `--pages` mount the contract does not declare or that names an `App · ` page, an empty `boundary-check.py --run`, a `journey.py run <name>` with no directory under `.mmw/journeys/`, a `CHECK:` that stubs the application's own network, a pipeline script called without `--contract`, with a flag its `--help` does not list, or with an address that belongs in `.mmw/target.json`, or a baseline-class source missing from `## Read first`).
_Avoid_: 问题标签
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`ERROR`, `WARN`**:
The two lint levels. gate-lint prints `ERROR` and `WARN `; `--lint`'s exit code says only whether an `ERROR` is left.
_Home_: `mmw-v2/skills/verify-ticket/references/linting.md`

**triage**:
The skill that moves an issue from outside through the state machine of triage roles: it reads the `needs-triage` queue, recommends one of the four outcomes (`needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix` — staying at `needs-triage` is not one), posts an agent brief at the evaluation stage, and ends every comment with the disclaimer. An issue judged to be agent work enters the landing pipeline through `to-spec` and then `to-tickets`; tickets `to-tickets` wrote are not triaged.
_Avoid_: 人拍板
_Home_: `mmw-v2/upstream/skills/engineering/triage/SKILL.md`

**morning**:
The user takes over with the two **morning queries**, in this order: `--state open --label needs-triage`, what fell over in the night, which `triage` is run over before anything else; then `--state open --label ready-for-human`, what only the user can do. The commands are in `docs/agents/issue-tracker.md`.
_Avoid_: 早上 (as a term), 早上两条查询, the two morning queries
_Home_: `docs/agents/issue-tracker.md`

### Values at a glance

| name | values |
| --- | --- |
| worker grade | `junior-worker` · `senior-worker` |
| `ABANDON:` kind | `failed` · `stuck` · `decision` |
| `ready-for-human` kind | `reaction` · `reach` |
| criterion state | `met` · `unmet` · `abandoned` |
| lint level | `ERROR` · `WARN` |
| layer label | `mmw:map` · `mmw:spec` · `mmw:ticket` · `mmw:child` |
| state role | `needs-triage` · `needs-info` · `ready-for-agent` · `ready-for-human` · `wontfix` |
| category role | `bug` · `enhancement` |
| `child.opened` kind | `finding` · `contract` · `deferred` · `decision` · `fault` |
| `child.closed` resolution | `fixed` · `stale` · `became-ticket` |
