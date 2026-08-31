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
The junior grade of worker. Its host, model and thinking effort are its row in `models.md`.
_Avoid_: 初级工人, 初级 worker

**senior-worker**:
The senior grade of worker. Its host, model and thinking effort are its row in `models.md`.
_Avoid_: 高级工人, 高级 worker

**verifier**:
The subagent a worker dispatches to re-run every acceptance criterion and write one `VERDICT`. It may install, re-port and reconfigure its environment, and changes no file in the repository.
_Avoid_: 复验者, verifier 子代理, subagent verifier

**reviewer**:
The session a worker starts through Herdr to run one round of code review.
_Avoid_: reviewer 会话, code-review 会话, 复核者

**dispatcher（派发者）**:
Inside code review, the role that starts the three reviewing subagents, collects all three reports, and writes the comment. It neither judges nor fixes anything itself.
_Avoid_: —

**host（宿主）**:
The command-line agent program a session runs on; the `host` column of `models.md`. Herdr calls it the agent kind.
_Avoid_: harness

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
The path globs this ticket is allowed to change. Paths it creates are marked `(new)`. The rule the ticket writer publishes by: no two tickets that could be started at the same time may have overlapping `## Owns`.
_Avoid_: —

**`## Acceptance criteria`**:
The numbered list of criteria.
_Avoid_: —

**`## Blocked by`**:
Which tickets must close before this one can start, written for the reader. The tracker's native blocking links are the copy the scripts read; `--lint` warns when the two disagree. When nothing blocks it, `None (can start immediately)`.
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

**frontier**:
The set of tickets `board.py` may start right now, in ticket order: open, labelled `ready-for-agent`, every blocker closed, no assignee, and no live session already holding it.
_Avoid_: 前沿

**spec**:
A top-level issue carrying a set of child tickets, as distinct from a ticket.
_Avoid_: 父票, spec 票

### Anatomy of a spec

**`## User Stories`**:
One line each, `As <role>, I want …, so that …`.
_Avoid_: —

**`## Implementation Decisions`**:
The decisions that were made, grouped into numbered subsections (`### 1. …`, `### 2. …`) that tickets point at by number. Every decision names where it came from at the end of the sentence or table row that states it — a decision ticket number, an ADR id, a research or prototype path, a user-story number — or says "this spec's decision".
_Avoid_: —

**`## Testing Decisions`**:
The first sentence names the seam: what is real on each side of it, and which external seams may be stubbed. Then test layer, then directory, then precedent, then the command to run before committing. `CHECK:` and `EXPECT:` are derived from here.
_Avoid_: —

**`## Out of Scope`**:
What this round explicitly does not do, and why.
_Avoid_: —

**`## Sources`**:
The first-hand material this spec was built from, in nine kinds — wayfinder map, decision tickets, upstream specs, ADRs, research files, prototype branches or directories, domain docs, evidence, test rules — one line per kind, and `none` where a kind has none, so a reader can tell "nothing there" from "forgot to list".
_Avoid_: —

**`## Further Notes`**:
Pace and anything outside scope that still has to be said.
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

**`CWD:`**:
The fourth attribute of a criterion: the working directory its `CHECK:` runs in. Changing it discards a result already recorded, the same way changing the command does.
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

**`gate`**:
What the judging engine calls a criterion, in the lines it prints and nowhere else. Prose says criterion.
_Avoid_: —

### Running the criteria

**账本（ledger）**:
The temporary file derived from the ticket body — or from the most recent `self-run` or `reverify` comment — that the gate checker reads. It is the only format the gate checker accepts.
_Avoid_: 临时账本

**`gate-check`**:
The judging engine vendored from unlazy (see `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`). Walks the ledger, runs each `CHECK:`, applies 双条件, writes `EVIDENCE:`.
_Avoid_: naming this role by its file name; write `gate-check.mjs` only when the file itself is meant

**`gate-lint`**:
The ticket-face linter vendored from unlazy (see `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`). Reports problems in how criteria are written; runs no command.
_Avoid_: naming this role by its file name; write `gate-lint.mjs` only when the file itself is meant

**`STALE`**:
What the gate checker reports when a criterion's `CHECK:`, `EXPECT:`, `CWD:` and shell signature no longer matches the one the run started with, so the result is discarded.
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

**gate-check summary line（gate-check 汇总行）**:
The last line the gate checker prints, copied into the second line of a `self-run` or `reverify` comment. Three shapes: `ALL MET (<n> met…)`, `UNMET: <n> (met: <m>)`, and `HANDOFF REQUIRED: <n> abandoned (met: …)`. A `reverify` adds `reran:` and `previously met reverified:` inside the parentheses. It is not the closing comment's first line: whether a comment is a closing comment is decided on that first line's own literal shape and nothing else.
_Avoid_: —

**`UNMET: <n> (met: <m>)`**:
One shape of the gate-check summary line: at least one criterion is not met.
_Avoid_: —

**`RUN` / `PASS` / `FAIL` / `STALE`**:
The per-criterion status lines, one printed for every criterion the run touches, whether or not `--reverify` was passed. Whatever did not pass is counted into the `UNMET:` summary line.
_Avoid_: —

**`UPSTREAM.md`**:
The note written whenever upstream scripts are vendored: source repository, commit, date, and which lines were changed.
_Avoid_: —

### The verdict

**`VERDICT`**:
The verifier's judgement comment, written `VERDICT <full 40-character commit> by <model> — <one line>`. The one line says what was run (a walked interface, commands only, or nothing would start), the result, and any environment repair.
_Avoid_: —

**`The environment is yours; the repository is not`**:
The heading in `mmw-v2/agents/verifier/body.md` that draws the verifier's boundary — it may install, re-port and reconfigure, and may change no file in the repository.
_Avoid_: —

### The closing comment

**closing comment（收尾评论）**:
The comment a worker leaves on handing over. Written to a draft file first, then posted by the closing gate.
_Avoid_: 收尾评论草稿, 草稿

**`ALL MET`**:
One of the two possible first lines: every criterion passed and the ticket may close. The same string also opens the gate-check summary line, as `ALL MET (<n> met…)`, on the second line of a `self-run` comment.
_Avoid_: —

**`HANDOFF REQUIRED`**:
The other first line, in full `HANDOFF REQUIRED: <n> abandoned (<kinds>), <m> unmet, <k> met of <total>`.
_Avoid_: 交人

**`Branch: … Commit: … PR: …`**:
The one line under the first line. When there is no pull request, `PR: none — <reason>`.
_Avoid_: —

**`Post-verdict:`**:
Every commit made after the last `VERDICT`, each with where it came from. `None` when the verdict is already on HEAD.
_Avoid_: —

**`Outside Owns:`**:
The files this ticket's own commits changed outside `## Owns` — merges from other branches excluded. Computed by the ticket script and copied into the draft; `None` when empty.
_Avoid_: —

**`skipped: [X], add when [Y]`**:
What was deliberately not built, and the condition under which to build it.
_Avoid_: —

**`Sub-issues opened:`**:
Every sub-issue this ticket opened under the spec, from all four sources: 契约装不下, a change outside `## Owns` that was merely convenient, an out-of-ticket code review finding, and an `ABANDON: decision` criterion.
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
The start-of-work guard. Checks six things — the branch, uncommitted tracked changes, the ticket's state, the `ready-for-agent` label, open blockers, and the assignee; only then claims the ticket.
_Avoid_: 开工核对

**`--closeout`（关票门）**:
The closing gate. Reads the draft and checks it against the ticket and the repository, and only then posts the comment and closes the ticket or swaps its label. Its checklist is in `mmw-v2/skills/verify-ticket/SKILL.md`.
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

**problem tag（问题标签）**:
What the linter labels each finding with, from three sources. The vendored `gate-lint`: `parse`, `tautological-check`, `weak-expect`, `path-read-as-regex`, `manual-gate`, `unmeasured-number`, `activity-not-outcome`, `mostly-manual`. `manual-gate` is a criterion with no `CHECK:` — a criterion in the wrong place, since nobody but its own author would decide it. This repository's `verify-ticket.py` adds four of its own: `dollar-without-m` (`ERROR`), `shared-state`, `unexplained-edge` and `cross-batch` (`WARN`). Its ticket-graph check reports `cycle`, `duplicate-ticket` and `blocker-not-a-ticket` as `ERROR`, and `cross-batch` — a blocker that is a ticket under another spec — as `WARN`, because a layered delivery is built on exactly those edges.
_Avoid_: —

**`ERROR` / `WARN`**:
The linter's two levels, and the only thing its exit code says is whether an `ERROR` is left. A ticket set converges when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.
_Avoid_: —

**启动层级（start levels）**:
The order in which tickets may be started, printed by the linter once the graph has no cycle and no dangling reference.
_Avoid_: —

**`HOOKS-INSTALLED`**:
The marker `install.sh` prints once the hooks are written, or checked and found in place.
_Avoid_: —

**`MMW_V2_HOME`**:
The environment variable that moves the whole install location to a throwaway directory, used when testing the installer.
_Avoid_: —

**`hook.py pretool`**:
The host-side enforcement of the closing gate: when a command tries to close a ticket or swap its label, it refuses outright and runs nothing — a worker typing `gh issue close` has by definition not been through `--closeout`.
_Avoid_: 关票 gate

**`rule-at-moment.py`**:
The Claude Code hook that puts the matching section of `~/.claude/CLAUDE.md` in front of the model at the moment it applies: the file's size before a `Read`, the next `offset` after the host truncates a result, rules 1, 3, 4 and 6 before a write, rule 5 after a failure, `## Before ending a turn` once per turn that used tools. It refuses one call only: an `Agent` call with no `model`.
_Avoid_: 规则提醒 hook, 拦截 hook, 注入 hook

### Dispatch

**`dispatch.sh <ticket> <role> [base-commit]`**:
One command that turns a ticket into a live session already carrying its ticket number, worktree and Herdr name.
_Avoid_: —

**`dispatch.sh wait <ticket> "<first-line-regex>" [seconds]`**:
Blocks until the first line of the ticket's last comment matches. On timeout it comments on the ticket first, then exits non-zero.
_Avoid_: —

**`models.md`**:
The one table defining, for every agent, its host, model, thinking effort and launch arguments.
_Avoid_: 角色表

**`issue-<n>` / `issue-<n>-review`**:
`issue-<n>` is the branch name of a worker's worktree. Its Herdr name is that with the workspace id in front — `w2q-issue-<n>` — because Herdr's names are unique among live agents across the whole server, and two repositories each holding a ticket #100 would otherwise collide. `issue-<n>-review` is only the reviewer's Herdr name, prefixed the same way; the reviewer cuts no branch and runs inside the worker's worktree. Outside Herdr the names are the bare ones.
_Avoid_: —

**`MMW_TICKET`**:
The ticket number injected into the session's environment when a worker is dispatched; a reviewer has none. It is the hook's only source for which ticket this session guards — no variable, no gate.
_Avoid_: —

**`phase`**:
A Herdr pane token holding the stage a worker is at. Six values — `selfcheck`, `verify`, `implement`, `closed`, `handoff`, `closeout-rejected` — all written by the ticket script.
_Avoid_: —

**`ticket` / `kind` / `ac` / `model` / `wake`**:
The other Herdr pane tokens. `ticket`, `kind` and `model` are written by `dispatch.sh` when it starts the session; `ac` is `<met>/<total>`, written by the ticket script; `wake` counts how many times `board.py` has re-prompted this session. The token `kind` takes two values only, `worker` and `reviewer`; `dispatch.sh`'s `<role>` argument is a different set — `junior-worker`, `senior-worker` or `reviewer`.
_Avoid_: —

**`working` / `idle` / `done` / `blocked` / `unknown`**:
Herdr's five lifecycle states for the agent in a pane, read from `herdr agent get` or `herdr api snapshot`. `blocked` is an approval or question form on screen; `unknown` is an agent Herdr cannot classify, or none at all.
_Avoid_: 在提问, 会话没了, 会话死了

**`idle` ∧ `phase` ∉ {`closed`, `handoff`}**:
A worker whose pane is `idle` or `done` while its `phase` is anything other than `closed` or `handoff`: it stopped before the closing gate. The judgement is the two tokens read together; nothing on screen is consulted.
_Avoid_: 半路停了, 半途停下, 没到终点就停了, 停在半路, 到终点, 终点, stalled

**re-prompt（重新 prompt）**:
Sending a session that has settled a new prompt with `herdr agent prompt`. A worker is re-prompted with `continue` and nothing else; the main agent is re-prompted with one line beginning `mmw board:`. Delivered only while the target is `idle` or `done` and its pane is not focused.
_Avoid_: 捡回, 叫醒, 唤醒 (the verb)

**唤醒闭环（wakeup loop）**:
The rule table `board.py --watch` applies after every pane event: leave `working` alone; on `idle` with `phase` other than `closed`/`handoff` wait `COOLDOWN_SECONDS` then re-prompt, up to `WAKE_LIMIT`; on `blocked` comment the form as `BLOCKED:`, dismiss it, then re-prompt; on `unknown` redispatch once; past any limit hand the ticket back to `needs-triage`.
_Avoid_: 捡回闭环

**夜间编排主循环（night orchestration loop）**:
Everything between the last ticket published and the morning: `dispatch.sh run` starts it, `board.py --watch` runs the 唤醒闭环 and writes `NIGHT SUMMARY` when nothing is left to run, and the main agent runs `dispatch.sh advance` whenever the board says the frontier has grown. Repair belongs to the board, the next step to the main agent.
_Avoid_: 夜间主循环, 夜里的循环

**`board.py`**:
The one resident program of the night, in the dispatch skill. `--once` prints one table and exits; with no argument it appends one line per event; `--watch <spec>` does the same and acts. It reads `herdr api snapshot` and `gh` each round and keeps no file.
_Avoid_: 常驻进程, 看板

**监控 tab（monitor tab）**:
The Herdr tab `dispatch.sh run` opens in its own workspace with the label `mmw board #<spec>`, where `board.py --watch` runs; its appended output is readable by `herdr pane read` and by a person. One per workspace, so a night on several projects has several of them.
_Avoid_: board tab, mmw board tab

**`dispatch.sh run <spec> [--role R] [--max-hours H]`**:
The one command that opens a night. It runs `install.sh --check` and refuses on any missing item, renames the main agent's pane `mmw-main`, opens the 监控 tab in this workspace and starts `board.py --watch` in it. It dispatches nothing; the main agent runs `dispatch.sh advance` straight after it.
_Avoid_: 开夜

**`dispatch.sh advance <spec> [--role R]`**:
The one command that moves a batch on: it merges the branch of every ticket that closed with `ALL MET`, oldest closing first and each keeping a merge commit, then dispatches every ticket on the frontier. The two are one command because a worktree is cut from `HEAD` when it opens, so a branch merged later is a branch the next ticket cannot see. Exit 3 leaves a conflict in the tree for the `resolving-merge-conflicts` skill and dispatches nothing; running it again after the resolution carries on from the next branch.
_Avoid_: —

**`mmw-main`**:
The Herdr name `dispatch.sh run` gives the main agent's own pane, so `board.py` can re-prompt it.
_Avoid_: —

**`mmw board: <case> #<n> — run <command>`**:
The one line `board.py` sends `mmw-main`. `<case>` is one of five literals. `ADVANCE` says the frontier has grown and `night over` says the night ended; both end in `dispatch.sh advance <spec>`, because both leave branches to merge. `WAKEUP LIMIT`, `REDISPATCHED` and `TIME LIMIT` say a limit was reached and the board has already commented and relabelled; they end in `board.py --once <spec>`, which the main agent reads and acts no further on. Either way it runs the command as written.
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
First lines of the comments `board.py` posts when it hands a ticket back to `needs-triage`: re-prompted `WAKE_LIMIT` times and it stopped again, or `MAX_HOURS` passed under this board's watch.
_Avoid_: —

**`NIGHT SUMMARY <date>`（夜间总结）**:
First line of the comment `board.py` posts on the spec when nothing is left to run: closed tickets, tickets handed back and their first lines, tickets not dispatched because a blocker stayed open, sub-issues opened during the night. Ticket numbers and first lines only.
_Avoid_: 早上总结

**`COOLDOWN_SECONDS` / `WAKE_BACKOFF` / `WAKE_LIMIT` / `REDISPATCH_LIMIT` / `MAX_HOURS` / `SNAPSHOT_INTERVAL`**:
The constants at the top of `board.py`: the wait before the first re-prompt, the growing waits after it, re-prompts per session, redispatches per ticket, hours per ticket, and the full re-read interval. There is no limit on how many tickets run at once — dispatching is the main agent's, and it is given no budget to spend.
_Avoid_: 并行上限, 冷却期, 退避

**dispatch line（派发词）**:
The one sentence a session is given when it is dispatched: which skill to use, on which ticket, and nothing else. The host discovers its installed skills by itself, so the sentence names a skill rather than a path. Everything fixed lives in the skill or in the definition file, never in that sentence. A session already running is not sent this sentence again; it is sent `continue`.
_Avoid_: —

**`Use the implement skill to work ticket #<n>`**:
The dispatch line for a worker.
_Avoid_: —

**`Use the code-review skill to review ticket #<n> from base commit <base-commit>`**:
The dispatch line for a reviewer.
_Avoid_: —

**`continue`**:
The whole of a re-prompt. The session it reaches is alive and still holds the skill it is running and the ticket it is on, so the word is the message: carry on from where you stopped.
_Avoid_: —

**`verify #<n>`**:
The prompt a worker gives its verifier. Nothing but the ticket number.
_Avoid_: —

**认领（claim）**:
Setting the ticket's assignee to oneself. Done by the start-of-work guard once its checks pass.
_Avoid_: —

### Code review

**`Standards reviewer` / `Spec reviewer` / `Tests reviewer`**:
The three read-only subagents of one code review, one per axis. Each name is the H1 of its file under `mmw-v2/upstream/skills/engineering/code-review/references/`. `reviewer` on its own always means the session a worker starts, never one of these three.
_Avoid_: —

**`Standards` axis**:
One of the three axes: does the change follow this repository's documented coding standards, and does the same outcome exist with less code.
_Avoid_: —

**`Spec` axis**:
The second axis: does the change match what the ticket or the spec asked for. It does not look at the handoff package.
_Avoid_: —

**`Tests` axis**:
The third axis: are the test cases the criteria name worth trusting. Its in-ticket scope is the test files and cases a `CHECK:` names; a test file in the diff that no `CHECK:` names still earns a finding, filed as out-of-ticket. It reports no coverage.
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

**`REVIEW <base commit>..<HEAD commit>`**:
The fixed first line of the review report comment.
_Avoid_: —

**base-commit（起点 commit）**:
The first argument of the review dispatch line: where the diff starts. Read from `git config branch.issue-<n>.mmw-base` in the worker's worktree — the cut point dispatch recorded when it opened the worktree, the same starting point `Outside Owns:` is measured from.
_Avoid_: —

### UI acceptance

**叶子目录（leaf directory）**:
`prototypes/<task>/<issue>/<UI|LOGIC|EXP>/`, one directory per kind of prototype. The handoff package and its `scenes.json` live in the `UI/` one.
_Avoid_: —

**`?variant=<winner>`**:
The query string of the prototype stage described in `mmw-v2/upstream/skills/engineering/prototype/UI.md`: it switches one real route between the variants under comparison, and comes down with the rest of the scaffolding once a winner is picked. A parity run puts a scene on the implementation page a different way — by turning that scene's `props` in `scenes.json` into the page's query string.
_Avoid_: —

**交接包（handoff package）**:
The five things step 7, **Finish**, of `mmw-v2/skills/claude-design-blocks/SKILL.md` downloads into the leaf directory: the component's `.dc.html`, `styles/`, `data/`, `support.js`, and `scenes.json`. The source to copy exact wording, sizes and tokens from, and the directory `visual-parity.py` renders and screenshots — on the command line it is written `--baseline`.
_Avoid_: 开发交接包, 基线目录, UI 基线

**`DESIGN.md`**:
The consuming repository's design-system document. When it is missing, it is generated before any design work starts.
_Avoid_: —

**场景（scene）**:
One entry of `scenes.json`, carrying a `name`, a `page` and its `props`. Each gets its own screenshot and its own accessibility tree.
_Avoid_: 场景列表

**`<dc-import name="…" scenario="…">`**:
The wrapper-page form that pins a scene and switches a design component into that state.
_Avoid_: scenario 属性

**`#dc-root`**:
The anchor the baseline side is screenshotted and read from. The implementation side takes the whole viewport and reads the accessibility tree of `body`.
_Avoid_: —

**ARIA 树（accessibility tree）**:
The page's accessibility tree. Compared scene by scene and viewport by viewport after normalisation; the difference must be zero.
_Avoid_: —

**归一化（normalisation）**:
The three rules that standardise an accessibility tree: drop `generic` and `group`, drop landmark names, and drop a `main` nested inside another `main`, lifting its children one level.
_Avoid_: —

**负控制（negative control）**:
One deliberately wrong scene, built once after every scene has run at the first viewport. It is judged before any of them: a run that did not catch it says nothing about the scenes it passed.
_Avoid_: —

**`PARITY OK <n>/<n>`**:
The single line printed when every scene at every viewport passed. Exit code 0.
_Avoid_: —

**`DIFF <scene> <viewport> <pct>% box=… — <reasons>`**:
The line printed for a scene and viewport that did not pass, ending in every reason it failed. Only an accessibility-tree difference brings lines out under it — `baseline` / `impl` for a changed node, `only in baseline` or `only in impl` for one on one side alone.
_Avoid_: —

**`NEGATIVE CONTROL FAILED`**:
The negative control did not fail, so this run's result cannot be trusted. Exit code 2.
_Avoid_: —

### Labels and standing

**`needs-triage`**:
Nobody has judged it yet: something arriving from outside, or a ticket an agent could not finish. `/triage` reads this queue and recommends one of four outcomes — `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. Full definition in `docs/agents/triage-labels.md`.
_Avoid_: —

**`needs-info`**:
Waiting on more information. Full definition in `docs/agents/triage-labels.md`.
_Avoid_: —

**`ready-for-agent`**:
In the agent queue. Full definition in `docs/agents/triage-labels.md`.
_Avoid_: —

**`ready-for-human`**:
In your queue, carrying one thing only a person can do, of kind `reaction` or `reach`. Full definition in `docs/agents/triage-labels.md`.
_Avoid_: —

**`reaction`**:
A kind of `ready-for-human` ticket: the property being asserted is a person's reaction, so the person is the measuring instrument and no agent can stand in. It cannot be engineered away.
_Avoid_: 人工项

**`reach`**:
A kind of `ready-for-human` ticket: a machine would decide it correctly if it could get to the thing — a device, a credential, a real environment. The ticket carries one line naming what would retire it. A pile of these means the pipeline is missing a capability, not that the user owes work.
_Avoid_: 只有人有的访问权

**`wontfix`**:
Will not be done. Full definition in `docs/agents/triage-labels.md`.
_Avoid_: —

**早上两条查询（the two morning queries）**:
The two issue-list queries the morning starts from: `is:open label:needs-triage`, everything that fell over in the night, which `/triage` gets a pass at first, and `is:open label:ready-for-human`, what only a person can do. The commands themselves are in `docs/agents/issue-tracker.md`.
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
Anything under `## Read first` that records a settled conclusion: the chosen artifact of a prototype — the winning UI variant until a handoff package supersedes it, the validated logic module, an experiment's Reusable parts with its Conclusion — a handoff package downloaded from Claude Design, the Decision of an ADR, the resolution of a decision ticket, and the spec sections `## Parent` names. Material recording process rather than conclusions — the body of a research file, a blueprint page — is working material, not baseline.
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

**写码纪律七条（the seven working rules）**:
The seven rules a worker writes code under: every baseline in `## Read first` is the contract, copied rather than written again from memory, 契约装不下 is answered with a sub-issue rather than a quiet change, and a check that will not pass is answered by fixing the code or abandoning the criterion rather than by bending the baseline, the harness or the test; before changing a function grep every caller and fix the shared code once, and before adding a branch or guard name the branch or file it makes unnecessary and delete it in the same commit; before writing a helper search the repository and `## Read first` for one that exists; before adding a file, a dependency or a configuration entry say why the existing one is not enough; never simplify away security, error handling that prevents data loss, accessibility, or anything the ticket names; at the end write `skipped: [X], add when [Y]`; and for a file outside `## Owns`, Owns 两档.
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

**消费仓库（consuming repository）**:
The outside repository where real tickets are run, as distinct from this toolbox repository.
_Avoid_: consumer repo

### Test layers

**结构核对（structural check）**:
Run `install.sh --check`, which already runs `assemble.py --check` inside it. Run `assemble.py --check` on its own only to check the assembled subagents and nothing else.
_Avoid_: —

**自写脚本层（own-script layer）**:
Scripts written in this repository are tested against fixed samples, with no real network calls: the Python ones with unittest, the bash ones as `tests/*.sh`. Each skill's entry point is its `tests/run.sh`.
_Avoid_: 自写脚本

**vendor 脚本层（vendored-script layer）**:
Run the tests that came with the vendored upstream scripts.
_Avoid_: vendor 脚本

**技能行为层（skill-behaviour layer）**:
Run the skill for real against a throwaway ticket made for the test inside a worktree, and check what appears on the ticket.
_Avoid_: 技能行为

**真票（real ticket）**:
The last layer: one real ticket carried from writing to closing. Nothing merges to the main branch until that passes.
_Avoid_: —
