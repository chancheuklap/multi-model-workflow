# Multi-Model Workflow

A toolbox of skills and subagents shared across hosts, repositories, and machines. Its core is a landing pipeline that carries one unit of work from a written spec, through a ticket, through an agent that writes the code, to a closed ticket with evidence attached. This glossary fixes the name of every term that pipeline invents, so that a session starting with an empty context uses the same word the last one used.

Terms whose name is itself a literal string that appears in a file, a comment, or a command have exactly one name — that string. Terms naming a role or a practice carry an English name and a Chinese name, given in parentheses; use the Chinese one in Chinese prose and the English one everywhere else.

## Language

### Roles

**main agent（主 agent）**:
The single Claude Code session that runs all day: by day it works with the user to produce specs and tickets, by night it dispatches workers and only reads tickets.
_Avoid_: coordinator, 编排者, orchestrator, 出票的主 agent, 落地 agent

**worker**:
An independent session dispatched to do one ticket, running the whole path from claiming the ticket to writing the closing comment.
_Avoid_: 工人, 做票的 agent, 领票的 agent

**junior-worker**:
The junior grade of worker, running on cursor.
_Avoid_: 初级工人, 初级 worker

**senior-worker**:
The senior grade of worker, running on grok.
_Avoid_: 高级工人, 高级 worker

**verifier**:
The read-only subagent a worker dispatches to re-run every acceptance criterion and write one `VERDICT`. It changes no file in the repository.
_Avoid_: 复验者, verifier 子代理, subagent verifier

**reviewer**:
The Claude Code session a worker starts through Herdr to run one round of code review.
_Avoid_: reviewer 会话, code-review 会话, 复核者

**dispatcher（派发者）**:
Inside code review, the role that starts the two reviewing subagents, collects both reports, and writes the comment. It neither judges nor fixes anything itself.
_Avoid_: —

**user（用户）**:
The only reader of a ticket no agent may stand in for — one labelled `ready-for-human`.
_Avoid_: 人, 你

### Anatomy of a ticket

**`## Parent`**:
The first section of a ticket. Points at the spec it belongs to and names the sections of that spec to read.
_Avoid_: —

**`## What to build`**:
The second section of a ticket. What to build, written as points rather than one block of prose.
_Avoid_: —

**`## Read first`**:
The list of material to read to a conclusion before starting work.
_Avoid_: —

**`## Seam`**:
Which layer this ticket is verified at, which directory the tests live in, and which existing file to copy the shape from.
_Avoid_: —

**`## Owns`**:
The path globs this ticket is allowed to change. Paths it creates are marked `(new)`.
_Avoid_: —

**`## Acceptance criteria`**:
The numbered list of criteria.
_Avoid_: —

**`## Blocked by`**:
Which tickets must close before this one can start. When nothing blocks it, `None (can start immediately)`.
_Avoid_: —

**`<issue-template>`**:
The tag inside the ticket-writing skill that defines the seven sections above.
_Avoid_: —

**`AC<n>:`**:
The number of one acceptance criterion. Fixed when the ticket is written and never renumbered.
_Avoid_: —

**`(new)`**:
The mark in `## Owns` saying this ticket creates that path.
_Avoid_: —

**directory glob（目录 glob）**:
The form `## Owns` takes when one ticket has a directory to itself. When several tickets divide one directory, `## Owns` goes down to file level instead.
_Avoid_: —

**`[fixture]` ticket（`[fixture]` 票）**:
Title prefix marking a ticket made to exercise the pipeline itself rather than to deliver anything.
_Avoid_: 虚构票, fixture 票

**落地 `<n>/15`**:
Title prefix saying which of the fifteen steps this ticket is.
_Avoid_: —

**frontier**:
The set of tickets that may be worked in parallel right now. The hard rule: no two tickets on one frontier may have overlapping `## Owns`.
_Avoid_: 前沿

**spec**:
A top-level issue carrying a set of child tickets, as distinct from a ticket.
_Avoid_: 父票, spec 票

### Anatomy of a spec

**`## User Stories`**:
One line each, `As <role>, I want …, so that …`.
_Avoid_: —

**`## Implementation Decisions`**:
The landing order. One change, one commit, one check per section.
_Avoid_: —

**`## Testing Decisions`**:
Test layer, then directory, then precedent, then the command to run before committing. `CHECK:` and `EXPECT:` are derived from here.
_Avoid_: —

**`## Out of Scope`**:
What this round explicitly does not do, and why.
_Avoid_: —

**`## Sources`**:
The map, decision tickets, ADRs and research files this spec rests on.
_Avoid_: —

**`## Further Notes`**:
Pace and anything outside scope that still has to be said.
_Avoid_: —

**我检查 / 你检查**:
The two kinds of check that close each section of `## Implementation Decisions`. 我检查 is what the main agent runs itself; 你检查 is what it hands the user to look at.
_Avoid_: —

**先例**:
The existing file `## Seam` points at, where the same shape of test is already written.
_Avoid_: —

**纵切**:
Tickets are cut by feature, not by front end against back end. That is why there are UI acceptance criteria but never a UI ticket.
_Avoid_: —

### Acceptance criteria

**五问（the five questions）**:
What a ticket writer asks of anything they want to say about the work, stopping at the first yes: is the rule a comparison against something a machine can reach (an acceptance criterion); is it a judgement against something a machine can reach (code review); is the property a person's reaction (`reaction`); could a machine decide it if it could reach the thing (`reach`); is it a choice rather than a check (a default plus a line in the closing comment, or a decision ticket asked earlier).
_Avoid_: 三条出路, 读者是谁

**`CHECK:`**:
The runnable command of one criterion. When it does not fit on one line it is followed by a fenced code block.
_Avoid_: —

**代码块围栏（fenced check）**:
The only way to write a multi-line `CHECK:`. A flush-left continuation line with no fence is a parse error.
_Avoid_: 隐式续行, 顶格续行

**`EXPECT:`**:
The marker that appears in the output of `CHECK:` only on success. A string, or a regex written `/…/flags`.
_Avoid_: —

**success-only marker**:
The rule `EXPECT:` is written to: the command prints that marker only when it succeeded.
_Avoid_: —

**`EVIDENCE:`**:
The one line of fact written after the criterion has been run. Until then, `pending`.
_Avoid_: —

**EVIDENCE structured line**:
The fixed shape the gate checker writes into `EVIDENCE:` — `exit=…; shell=…; cwd=…; path=…; EXPECT=matched; output-sha256=…; output-bytes=…`.
_Avoid_: —

**`ABANDON:`**:
The mark that opens the line of a criterion given up on, written `ABANDON: AC<n> <kind> <reason>`.
_Avoid_: —

**`failed`**:
An `ABANDON` kind: it ran and did not pass — three self-runs did not fix it, or it still failed after the one round of review fixes. The closing gate asks the ticket for those three self-run comments before it accepts this kind.
_Avoid_: —

**`stuck`**:
An `ABANDON` kind: the command will not start, a credential is missing, a device is needed, or the work is out of reach within the scope. The reason must list the routes already tried, or point at the sub-issue that records it. No round count is asked of it — it may be given up on the first time.
_Avoid_: blocked, impossible

**`decision`**:
An `ABANDON` kind: a person has to settle one sentence. A sub-issue is opened under `needs-triage` and the rest of the ticket continues; this kind alone does not force `HANDOFF REQUIRED`.
_Avoid_: —

**双条件（both conditions）**:
What it means for a criterion to pass: exit code 0 **and** the `EXPECT:` marker matched.
_Avoid_: —

**撤销**:
The end state of a criterion whose premise no longer holds, written in the criterion line in place of passed or failed.
_Avoid_: —

### Running the criteria

**账本（ledger）**:
The temporary file derived from the ticket body — or from the most recent `self-run` or `reverify` comment — that the gate checker reads. It is the only format the gate checker accepts.
_Avoid_: 临时账本

**`gate-check`**:
The judging engine vendored from upstream. Walks the ledger, runs each `CHECK:`, applies 双条件, writes `EVIDENCE:`.
_Avoid_: `gate-check.mjs`

**`gate-lint`**:
The ticket-face linter vendored from upstream. Reports problems in how criteria are written; runs no command.
_Avoid_: `gate-lint.mjs`

**`STALE`**:
What the gate checker reports when the signature of a `CHECK:` no longer matches the one it started with, so the result is discarded.
_Avoid_: —

**`self-run`（自跑）**:
The first line of the comment a worker's own run puts on the ticket.
_Avoid_: —

**`ROUND LIMIT`**:
The line a self-run adds when a criterion has come back unmet for the third time. It names the criterion and says to abandon it as `failed` and carry on. The rounds are counted off the ticket's own `self-run` comments; nothing is stored between runs, and a fourth run that finally passes still passes.
_Avoid_: —

**`reverify`（复验）**:
The first line of the comment the verifier's run puts on the ticket, where criteria already ticked are run again.
_Avoid_: 重验

**`UNMET: <n> (met: <m>)`**:
The second line of a `self-run` or `reverify` comment. A `reverify` adds `reran:` and `previously met reverified:`.
_Avoid_: —

**`PASS AC:AC<n>`**:
The compact per-criterion status printed after a re-run.
_Avoid_: —

**`UPSTREAM.md`**:
The note written whenever upstream scripts are vendored: source repository, commit, date, and which lines were changed.
_Avoid_: —

### The verdict

**`VERDICT`**:
The verifier's judgement comment, written `VERDICT <full 40-character commit> <level> by <model> — <one line>`.
_Avoid_: —

**level**:
The one field of `VERDICT` the verifier has to judge, chosen from five values.
_Avoid_: 模型级别, 判定类型, 核验等级

**`live-ui-verified`**:
A level: the flow was walked in a running interface and all of it passed.
_Avoid_: —

**`unit-test-verified`**:
A level: every command passed, no interface was started.
_Avoid_: —

**`type-check-only`**:
A level: only a type check passed. A ticket that changes behaviour does not pass on this.
_Avoid_: —

**`verifier-blocked`**:
A level: the commands still would not start after the verifier repaired its own environment.
_Avoid_: —

**`verifier-failed`**:
A level: the commands ran and at least one did not pass.
_Avoid_: —

**`self-reported`**:
What the `by` field of `VERDICT` degrades to when no subagent could be dispatched.
_Avoid_: —

**`The environment is yours; the repository is not.`**:
The line in the verifier's definition file that draws its boundary — it may install, re-port and reconfigure, and may change no file in the repository.
_Avoid_: —

### The closing comment

**closing comment（收尾评论）**:
The comment a worker leaves on handing over. Written to a draft file first, then posted by the closing gate.
_Avoid_: 收尾评论草稿, 草稿

**`ALL MET`**:
One of the two possible first lines: every criterion passed and the ticket may close.
_Avoid_: —

**`HANDOFF REQUIRED`**:
The other first line, in full `HANDOFF REQUIRED: <n> abandoned (<kinds>), <m> unmet, <k> met of <total>`.
_Avoid_: 交人

**`Branch:` / `Commit:` / `PR:`**:
The three lines under the first line. When there is no pull request, `none` plus the reason.
_Avoid_: —

**`Post-verdict:`**:
Every commit made after the last `VERDICT`, each with where it came from. `None` when the verdict is already on HEAD.
_Avoid_: —

**`Outside Owns:`**:
The files changed outside `## Owns`. Computed by the ticket script and copied into the draft; `None` when empty.
_Avoid_: —

**`skipped: [X], add when [Y]`**:
What was deliberately not built, and the condition under which to build it.
_Avoid_: —

**`Sub-issues opened:`**:
The sub-issues opened for `ABANDON: decision` criteria.
_Avoid_: —

**`Counts:`**:
The recounted tally, `<k> met, <m> unmet, <n> abandoned of <total>`.
_Avoid_: —

**`Decisions I made on my own`（本票我自己拿的主意）**:
The closing section listing everything the worker settled itself because neither the ticket nor the spec said.
_Avoid_: —

### Script subcommands

**`verify-ticket.py`**:
One script carrying five jobs: linting a ticket, the worker's own run, the verifier's re-run, the start-of-work guard, and closing the ticket.
_Avoid_: —

**`--preflight`（开工守卫）**:
The start-of-work guard. Checks branch, working tree, ticket state, blockers and assignee; only then claims the ticket.
_Avoid_: 开工核对

**`--closeout`（关票门）**:
The closing gate. Reads the draft, checks ten things, and only then posts the comment and closes the ticket or swaps its label.
_Avoid_: —

**`--lint`（票图核对）**:
Checks how criteria are written, plus cycles and dangling references across the tickets of one spec, and prints the 启动层级.
_Avoid_: —

**`--reverify`**:
Runs criteria that are already ticked as well.
_Avoid_: —

**`--check-only`**:
A dry run of `--closeout`: judges only, posts nothing, closes nothing.
_Avoid_: —

**`NOT_READY:`**:
The first line the start-of-work guard puts on the ticket and prints when it refuses. A worker that sees it stops.
_Avoid_: —

**`CLOSEOUT OK`**:
What the dry run prints when everything passes.
_Avoid_: —

**`HANDED BACK: #<n> is now needs-triage and stays open`**:
What the closing gate prints when it hands the ticket back to be judged fresh.
_Avoid_: —

**`cycle` / `dangling` / `dollar-without-m` / `manual-gate` / `shared-state`**:
The problem tags the linter reports. Errors: a cycle in the ticket graph, a reference to a ticket that is not there, an `EXPECT:` regex anchor that can never match, and a criterion with no `CHECK:` — which is a criterion in the wrong place, since nobody but its own author would decide it. A warning: a `CHECK:` that changes shared state.
_Avoid_: —

**`ERROR` / `WARN`**:
The linter's two levels, and the only thing its exit code says is whether an `ERROR` is left. A ticket set converges when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.
_Avoid_: —

**启动层级（start levels）**:
The order in which tickets may be started, printed by the linter once the graph has no cycle and no dangling reference.
_Avoid_: —

**`HOOKS-INSTALLED`**:
The marker the installer prints after its own check of the hooks it just wrote.
_Avoid_: —

**`MMW_V2_HOME`**:
The environment variable that moves the whole install location to a throwaway directory, used when testing the installer.
_Avoid_: —

**`hook.py pretool`**:
The host-side enforcement of the closing gate: when a command tries to close a ticket or swap its label, it runs the dry run and refuses on a non-zero exit.
_Avoid_: 关票 gate

### Dispatch

**`dispatch.sh <ticket> <role> [base-commit]`**:
One command that turns a ticket into a live session already carrying its ticket number, worktree and Herdr name.
_Avoid_: —

**`dispatch.sh wait <ticket> "<first-line-regex>" [seconds]`**:
Blocks until the first line of the ticket's last comment matches. On timeout it comments on the ticket first, then exits non-zero.
_Avoid_: —

**`models.md`**:
The one table defining, for every agent, its host, model, thinking effort and launch command.
_Avoid_: 角色表

**`issue-<n>` / `issue-<n>-review`**:
The Herdr name and branch name of a worker and of its reviewer. Must be unique among live agents.
_Avoid_: —

**`MMW_TICKET`**:
The ticket number injected into the session's environment at dispatch. The first place a hook looks for it.
_Avoid_: —

**`phase`**:
A Herdr pane token holding the stage a worker is at. Six values — `selfcheck`, `verify`, `implement`, `closed`, `handoff`, `closeout-rejected` — all written by the ticket script.
_Avoid_: —

**`ticket` / `role` / `ac` / `model` / `wake`**:
The other Herdr pane tokens. `ticket`, `role` and `model` are written by `dispatch.sh` when it starts the session; `ac` is `<met>/<total>`, written by the ticket script; `wake` counts how many times `board.py` has re-prompted this session.
_Avoid_: —

**`working` / `idle` / `done` / `blocked` / `unknown`**:
Herdr's five lifecycle states for the agent in a pane, read from `herdr agent get` or `herdr api snapshot`. `blocked` is an approval or question form on screen; `unknown` is an agent Herdr cannot classify, or none at all.
_Avoid_: 在提问, 会话没了, 会话死了

**`idle` ∧ `phase` ∉ {`closed`, `handoff`}**:
A worker whose pane is `idle` or `done` while its `phase` is anything other than `closed` or `handoff`: it stopped before the closing gate. The judgement is the two tokens read together; nothing on screen is consulted.
_Avoid_: 半路停了, 半途停下, 没到终点就停了, 停在半路, 到终点, 终点, stalled

**re-prompt（重新 prompt）**:
Sending a session that has settled a new prompt with `herdr agent prompt`. A worker is re-prompted with its dispatch line and nothing else; the main agent is re-prompted with one line beginning `mmw board:`. Delivered only while the target is `idle` or `done` and its pane is not focused.
_Avoid_: 捡回, 叫醒, 唤醒 (the verb)

**唤醒闭环（wakeup loop）**:
The rule table `board.py --watch` applies after every pane event: leave `working` alone; on `idle` with `phase` other than `closed`/`handoff` wait `COOLDOWN_SECONDS` then re-prompt, up to `WAKE_LIMIT`; on `blocked` comment the form as `BLOCKED:`, dismiss it, then re-prompt; on `unknown` redispatch once; past any limit hand the ticket back to `needs-triage`.
_Avoid_: 捡回闭环

**夜间编排主循环（night orchestration loop）**:
Everything between the last ticket published and the morning: `dispatch.sh run` starts it, `board.py --watch` dispatches the frontier, runs the 唤醒闭环, and writes `NIGHT SUMMARY` when nothing is left to run.
_Avoid_: 夜间主循环, 夜里的循环

**`board.py`**:
The one resident program of the night, in the dispatch skill. `--once` prints one table and exits; with no argument it appends one line per event; `--watch <spec>` does the same and acts. It reads `herdr api snapshot` and `gh` each round and keeps no file.
_Avoid_: board, 常驻进程, 看板

**监控 tab（monitor tab）**:
The Herdr tab `dispatch.sh run` opens with the label `mmw board`, where `board.py --watch` runs; its appended output is readable by `herdr pane read` and by a person.
_Avoid_: board tab, mmw board tab

**`dispatch.sh run <spec> [--role R] [--parallel N] [--max-hours H]`**:
The one command the main agent types at night. It runs `install.sh --check` and refuses on any missing item, renames the main agent's pane `mmw-main`, opens the 监控 tab and starts `board.py --watch` in it.
_Avoid_: 开夜

**`mmw-main`**:
The Herdr name `dispatch.sh run` gives the main agent's own pane, so `board.py` can re-prompt it.
_Avoid_: —

**`mmw board: <case> #<n> — run board.py --once`**:
The one line `board.py` sends `mmw-main`, only when a limit was reached or the night ended. The main agent answers it by running `board.py --once` and reading; it takes no other action.
_Avoid_: —

**`BLOCKED:`**:
First line of the comment `board.py` posts on a ticket whose worker is `blocked`, followed by the text of the form on screen.
_Avoid_: QUESTION:

**重派（redispatch）**:
Starting a new worker session for a ticket whose previous session is `unknown` or whose pane is gone while the ticket is still open with no closing comment. Once per ticket; the count is the ticket's `REDISPATCHED:` comments.
_Avoid_: —

**`REDISPATCHED:`**:
First line of the comment `board.py` posts before it redispatches, naming the phase the previous session ended at.
_Avoid_: —

**`WAKEUP LIMIT:` / `TIME LIMIT:`**:
First lines of the comments `board.py` posts when it hands a ticket back to `needs-triage`: re-prompted `WAKE_LIMIT` times and it stopped again, or `MAX_HOURS` passed since dispatch.
_Avoid_: —

**`NIGHT SUMMARY <date>`（夜间总结）**:
First line of the comment `board.py` posts on the spec when nothing is left to run: closed tickets, tickets handed back and their first lines, tickets not dispatched because a blocker stayed open, sub-issues opened during the night. Ticket numbers and first lines only.
_Avoid_: 早上总结

**`PARALLEL` / `COOLDOWN_SECONDS` / `WAKE_BACKOFF` / `WAKE_LIMIT` / `REDISPATCH_LIMIT` / `MAX_HOURS` / `SNAPSHOT_INTERVAL`**:
The constants at the top of `board.py`: tickets in flight at once, the wait before the first re-prompt, the growing waits after it, re-prompts per session, redispatches per ticket, hours per ticket, and the full re-read interval.
_Avoid_: 并行上限, 冷却期, 退避

**dispatch line（派发词）**:
The one sentence a dispatched session is given: the skill name plus the ticket number, and nothing else. Everything fixed lives in the skill or in the definition file, never in that sentence. A re-prompt sends the same sentence again.
_Avoid_: —

**`implement #<n>`**:
The dispatch line for a worker: skill name plus ticket number.
_Avoid_: —

**`code-review <base-commit> #<n>`**:
The dispatch line for a reviewer.
_Avoid_: —

**`verify #<n>`**:
The prompt a worker gives its verifier. Nothing but the ticket number.
_Avoid_: —

**认领（claim）**:
Setting the ticket's assignee to oneself. Done by the start-of-work guard once its checks pass.
_Avoid_: —

### Code review

**`Standards` axis**:
One of the three axes: does the change follow this repository's documented coding standards, and does the same outcome exist with less code.
_Avoid_: —

**`Spec` axis**:
The second axis: does the change match what the ticket or the spec asked for. It does not look at the handoff package.
_Avoid_: —

**`Tests` axis**:
The third axis: are the test cases the criteria name worth trusting. It reads only the test files named by a `CHECK:`, and reports neither coverage nor a test the criteria never asked for.
_Avoid_: —

**smell baseline**:
The list of code smells the `Standards` axis works from, carried in full inside its reference file.
_Avoid_: —

**test smell baseline**:
The list of bad-test shapes the `Tests` axis works from, carried in full inside its reference file.
_Avoid_: —

**票内 / 票外（in-ticket / out-of-ticket）**:
The two classes a review finding falls into, decided by whether it touches this ticket's criteria or a spec decision. In-ticket findings get one round of fixes; out-of-ticket findings become sub-issues.
_Avoid_: 票内发现, 票外发现

**`REVIEW <base-commit>..<HEAD commit>`**:
The fixed first line of the review report comment.
_Avoid_: —

**base-commit（起点 commit）**:
The first argument of the review dispatch line: where the diff starts.
_Avoid_: —

### UI acceptance

**叶子目录（leaf directory）**:
`prototypes/<task>/<issue>/UI/`, where the handoff package and the scene list live.
_Avoid_: —

**交接包（handoff package）**:
What the Finish step of the design skill downloads: a README plus every component page. The source to copy exact wording, sizes and tokens from, and the directory `visual-parity.py --baseline` renders and screenshots.
_Avoid_: 开发交接包, 基线目录, UI 基线

**`DESIGN.md`**:
The consuming repository's design-system document. When it is missing, it is generated before any design work starts.
_Avoid_: —

**场景（scene）**:
One state listed in the scene list. Each gets its own screenshot and its own accessibility tree.
_Avoid_: 场景列表

**`<dc-import name="…" scenario="…">`**:
The wrapper-page form that pins a scene and switches a design component into that state.
_Avoid_: scenario 属性

**`#dc-root`**:
The anchor selector for screenshots and for reading the accessibility tree.
_Avoid_: —

**`?variant=<winner>`**:
The query string that switches a real page's mount point to the winning prototype variant.
_Avoid_: —

**ARIA 树（accessibility tree）**:
The page's accessibility tree. Compared scene by scene and viewport by viewport after normalisation; the difference must be zero.
_Avoid_: —

**归一化（normalisation）**:
The three rules that standardise an accessibility tree: drop `generic` and `group`, drop landmark names, lift a nested `main` to the top.
_Avoid_: —

**负控制（negative control）**:
Every run first compares one deliberately wrong scene, to prove the tool itself is not broken.
_Avoid_: —

**`PARITY OK <n>/<n>`**:
The single line printed when every scene at every viewport passed. Exit code 0.
_Avoid_: —

**`DIFF <scene> <viewport> <pct>% box=…`**:
The line printed for a scene and viewport that did not pass, followed by the `baseline` and `impl` lines of the accessibility tree that changed.
_Avoid_: —

**`NEGATIVE CONTROL FAILED`**:
The negative control did not fail, so this run's result cannot be trusted. Exit code 2.
_Avoid_: —

### Labels and standing

**`needs-triage`**:
Nobody has judged it yet: something arriving from outside, or a ticket an agent could not finish. The one queue a skill picks up on its own — `/triage` reads it and recommends one of the four outcomes.
_Avoid_: —

**`needs-info`**:
Waiting on more information.
_Avoid_: —

**`ready-for-agent`**:
In the agent queue — waiting to be dispatched, or being worked right now; the assignee says which. Taken off at both exits, whether the ticket closes or is handed back.
_Avoid_: —

**`ready-for-human`**:
In your queue: a ticket carrying one thing only a person can do, of kind `reaction` or `reach`, naming what to look at and what makes it right. Applied when the ticket is written, or by triage once it has judged.
_Avoid_: —

**`reaction`**:
A kind of `ready-for-human` ticket: the property being asserted is a person's reaction, so the person is the measuring instrument and no agent can stand in. It cannot be engineered away.
_Avoid_: 人工项

**`reach`**:
A kind of `ready-for-human` ticket: a machine would decide it correctly if it could get to the thing — a device, a credential, a real environment. The ticket carries one line naming what would retire it. A pile of these means the pipeline is missing a capability, not that the user owes work.
_Avoid_: 只有人有的访问权

**`wontfix`**:
Will not be done.
_Avoid_: —

**早上五条查询（the five morning queries）**:
The fixed set of issue-list queries used to survey the tickets from outside the pipeline: handed to a human, closed yesterday, claimed by me and still open, newly triaged under a spec, and blocked.
_Avoid_: —

### Working discipline

**读法收窄（narrowed reading）**:
A worker does not read a whole spec. It follows `## Parent` to the sections that spec names, plus `## Testing Decisions` and `## Out of Scope`.
_Avoid_: —

**说出 Seam（state the seam）**:
The last step before writing code: say what this ticket's `## Seam` is. When the ticket has none, derive one from `## Testing Decisions` and comment it on the ticket.
_Avoid_: —

**Owns 核对（owns check）**:
A start-of-work step: every glob in `## Owns` either matches an existing path or is marked `(new)`.
_Avoid_: —

**基线（baseline）**:
Anything under `## Read first` that records a settled conclusion: the chosen artifact of a prototype — the winning UI variant until a handoff package supersedes it, the validated logic module, an experiment's Reusable parts with its Conclusion — a handoff package downloaded from Claude Design, the Decision of an ADR, the resolution of a decision ticket, and the spec sections `## Parent` names. Material recording process rather than conclusions — the body of a research file, a blueprint page — is reference, not baseline.
_Avoid_: —

**契约（contract）**:
The bond between a worker and every baseline in `## Read first`, in three clauses: copy exact values, wording, states and interface shapes from the baseline instead of rewriting them from memory; never deviate quietly — when the work does not fit the baseline or two baselines conflict, keep going and open a sub-issue under the spec; never bend a baseline, a harness or a test to make a check pass.
_Avoid_: —

**基线是契约（the baseline is the contract）**:
Every baseline in `## Read first` is a contract, not a reference. It is never quietly changed or quietly deviated from.
_Avoid_: —

**契约装不下（the contract does not fit）**:
When a baseline is missing a state, a field, an interaction or a case the work needs, or two baselines conflict: keep going, open a sub-issue under the spec, add nothing quietly.
_Avoid_: —

**Owns 两档（the two grades of Owns）**:
For a file outside `## Owns` — change it and record it under `Outside Owns:` when a criterion cannot pass otherwise; leave it alone and open a sub-issue when the change is merely convenient.
_Avoid_: 为过 AC 不得不改, 顺手改动

**ponytail 五句（the five sentences）**:
The five things to do before writing code: grep every caller before changing a function, and delete what a new branch makes unnecessary before adding it; look for something existing before writing a helper; say why what exists is not enough before adding a file, a dependency or a configuration; never simplify away four named things; write `skipped: [X], add when [Y]` at the end.
_Avoid_: —

**收尾七步（the seven closing steps）**:
Own run, verifier, one round of review, `Audit`, cut sub-issues and write the draft, push and open the pull request, closing gate.
_Avoid_: —

**`Audit`（交接前自审）**:
Re-read the whole ticket and every item of `## Read first`, trace every criterion to its latest `EVIDENCE:`, recount `Counts:`.
_Avoid_: —

**三轮上限（the three-round cap）**:
One criterion gets at most three rounds of fix-and-rerun. Still failing on the third, write `ABANDON: AC<n> failed` and move on to the rest.
_Avoid_: —

**merge-note**:
The note written or updated whenever a skill inside the upstream subtree is changed.
_Avoid_: —

**先验（probe first）**:
Settle one uncertain technical question before starting, and write the answer into the code comment and onto the ticket.
_Avoid_: —

**消费仓库（consuming repository）**:
The outside repository where real tickets are run, as distinct from this toolbox repository.
_Avoid_: consumer repo

### Test layers

**结构核对（structural check）**:
Run the installer's own check and the subagent assembler's own check.
_Avoid_: —

**自写脚本层（own-script layer）**:
Scripts written in this repository are tested with unittest against fixed samples; no real network calls.
_Avoid_: 自写脚本

**vendor 脚本层（vendored-script layer）**:
Run the tests that came with the vendored upstream scripts.
_Avoid_: vendor 脚本

**技能行为层（skill-behaviour layer）**:
Run the skill for real against a `[fixture]` ticket inside a worktree and check what appears on the ticket.
_Avoid_: 技能行为

**真票（real ticket）**:
The last layer: one real ticket carried from writing to closing. Nothing merges to the main branch until that passes.
_Avoid_: —
