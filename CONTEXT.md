# Multi-Model Workflow

A toolbox of skills shared across hosts, repositories, and machines. Its core is the landing pipeline: one unit of work travels from a written spec, through a ticket, through an agent that writes the code, to a closed ticket with evidence attached. This file fixes the name of everything the pipeline invents, so that a session starting with an empty context uses the same word the last one used.

How to read an entry: the bold line is the term's only name; a term whose name is a literal string that appears in a file, a command, or a comment is named by that string exactly (case, colon, and all). The definition says what the thing is and what sets it apart from its neighbours. `_Admitted_` lists the one other wording that may appear in prose. `_Avoid_` lists dead words: a sentence in this repository that uses one is wrong; an item followed by a note in parentheses says in which sense the word is dead. `_Home_` is the file whose text or code the definition is taken from; when this file and that one disagree, that one is right and this file is rewritten. An attribute that can be had by reading that file — a field list, an exit code, a command's switches, the branches of a behaviour — is not repeated here: an entry says what the term is and how it differs from its neighbours, and points at `_Home_` for the rest.

Vocabulary that belongs to one skill alone — `exe-release`'s release key, tiers, build machine and hooks; `claude-design-blocks`'s page kinds and helpers; `manage-agents-md`'s survey entries; `code-checkers`'s per-language checkers, their versions, and the file that silences a repository's existing errors; the design vocabulary of upstream skills such as `codebase-design` — is defined in that skill's own files and is not repeated here.

## Language

### Roles

**agent**:
Any session or subagent this pipeline sends out or runs: the main agent, a worker, a reviewer, the verifier, the advisor, a code-review axis subagent.
_Avoid_: board
_Home_: `~/.mmw/models.md`

**session**:
A host process a runner started, or the main agent the user started themselves. It carries a host. A session `dispatch.sh start` started is named on its ticket by its started event — `worker.started`, `reviewer.started` or `verifier.started` — whose payload carries the runner that runs it and that runner's own id for it, always as a pair. The main agent, a worker, a reviewer, the verifier, and the advisor are sessions; the three code-review axis subagents are not — they are subagents inside the reviewer session.
_Avoid_: 会话 (as a term), pane, terminal (for this)
_Home_: `~/.mmw/models.md`

**main agent**:
The session the user started themselves. By day it works with the user to produce specs and tickets; by night it runs `check`, then `open`, then `advance`, then on each **wake** `status`, one `advance` and `ack`, the **收口轮** when the frontier is empty and open `finding` children remain, then `reverify` and `summary`, and only reads tickets. It is the one agent with no row in the live table; it is tied to no host. One main agent holds one spec.
_Avoid_: coordinator, orchestrator, 编排者, 主 agent, 出票的主 agent, 落地 agent, the single Claude Code session, mmw-main, board
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**worker**:
An independent session dispatched to do one ticket, running the whole path from claiming the ticket to writing the closing comment. It runs the `implement` skill; its only input is the ticket; it owns the `issue-<n>` workspace, worktree and branch; it starts its verifier and its reviewer; it never closes the ticket by hand.
_Admitted_: worker session
_Avoid_: 工人, 做票的 agent, 领票的 agent, MMW_TICKET
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**worker grade**:
Which of the two workers a ticket goes to. Each grade is at once a ticket label and a row of the live table; the user sees it once, as the `Worker:` line of the `to-tickets` quiz, and the label is read afresh every time the ticket is started.
_Avoid_: grade of worker, seat, lane (for this)
_Home_: `~/.mmw/models.md`

**`junior-worker`**:
The default worker grade (`DEFAULT_WORKER` in `dispatch.sh`).
_Avoid_: 初级工人, 初级 worker
_Home_: `~/.mmw/models.md`

**`senior-worker`**:
The worker grade a ticket names when getting it wrong would be wrong silently.
_Avoid_: 高级工人, 高级 worker
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**reviewer**:
The session a worker starts with `dispatch.sh start <n> reviewer` to run one round of code review. It runs in the ticket's worktree, the worker's own, and cuts no branch; its report is the **review comment**, which the worker reads off the ticket. The worker does not stop it: landing does, together with every other session the ticket's started events name, when it archives the workspace (`land <n>` for one ticket, `advance` for a batch). On its own, `reviewer` always means this session, never one of the three axis subagents.
_Admitted_: reviewer session
_Avoid_: reviewer 会话, code-review 会话, 审稿人, MMW_AUTONOMOUS
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**dispatcher**:
The role the reviewer session takes once it holds the `code-review` skill: it starts the three axis subagents, sorts every review finding into in-ticket or out-of-ticket by the six conditions in `references/session.md` section 3, and writes the one review comment. It reviews nothing and fixes nothing itself. The session reads `references/session.md`; each axis takes the matching axis door of the same skill. `SKILL.md` is the shared door.
_Avoid_: 派发 (as a term)者
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**verifier**:
The session a worker starts last of its closing steps, once, with the prompt `Use the verdict skill to verify ticket #<n>` plus the two standing sentences every dispatched agent gets. In the same worktree on the same commit it re-runs every acceptance criterion with `--reverify` and posts one verdict with `verify-ticket.py <n> --verdict`: a `verifier.passed` or `verifier.failed` event. It runs after the last commit, because `--closeout` requires the verdict's commit to be `HEAD`; that one round is the whole of it, and a `verifier.failed` ends in a `HANDOFF REQUIRED`. It may repair its own environment and changes no file in the repository; it never starts the product by hand and never writes an `ABANDON:` line.
_Avoid_: 复验者, verifier 子代理, subagent verifier
_Home_: `mmw-v2/skills/verdict/SKILL.md`

**advisor**:
The second-opinion agent on a stronger model; it implements nothing. One door: a session from the advisor row of the live table, started by whichever agent hit the decision, its first prompt naming the `advisor` skill plus the **question packet**; how it is started is the skill's `references/consulting.md`. Nothing but its own instructions holds it to reading — a session on any host can write through a shell.
_Home_: `mmw-v2/skills/advisor/SKILL.md`

**question packet**:
What a caller hands the advisor, and the only thing the advisor sees: the recent user/assistant exchange quoted, the caller's current understanding, the constraints, the options weighed, and the file paths believed relevant. It carries the decision and the evidence; what to read and what to conclude stay the advisor's.
_Avoid_: 问题包, advisor prompt, brief
_Home_: `mmw-v2/skills/advisor/references/consulting.md`

**recommendation**:
What one consultation of the advisor gives back: do X, not Y, because Z, plus the single risk that decides it.
_Avoid_: verdict (for this)
_Home_: `mmw-v2/skills/advisor/references/advising.md`

**host**:
The command-line agent program a session runs on: one of `claude`, `codex`, `grok`, `cursor`, `pi`. It is the `host` column of the live table. Each host has its own install locations, hook configuration, form close key, and effort spelling.
_Avoid_: 宿主, agent kind
_Home_: `mmw-v2/skills/drive-target/scripts/hook.py`

**runner**:
The program that runs the sessions this pipeline starts on this machine: `paseo`, `orca` or `herdr`, one adapter each, `scripts/runners/<runner>.sh` of the dispatch skill. The adapter answers the three verbs the protocol asks of a runner — start a session in the directory it is given (`start`), deliver a message to one (`send`), say whether one is alive (`liveness`, whose third answer `unknown` is what it says when it cannot prove `alive` or `stopped`) — plus `stop` to end one and `self` to name the session the calling process runs in, and nothing else; its `# MMW_USES:` lines name the runner commands it calls, and `install.sh --check` holds them against the binary. It is not the host: the host is the agent program a session runs, the runner is what keeps it running and reachable. The worktree is not its either: `dispatch.sh` cuts and removes it with git and hands the runner only the absolute path. Tonight's runner is `python3 models.py runner` — `MMW_RUNNER`, then the live table's `runner` row, then the runner this process runs in when an adapter exists for it, then `orca`; the live table's rows are resolved against that runner's catalog (Paseo's own provider catalog on Paseo, each host CLI's own catalog on the other two). Once a session is started, every later command asks the runner its started event names, and no other.
_Avoid_: backend, night-process host, 夜间进程宿主, host (for this)
_Home_: `mmw-v2/skills/dispatch/scripts/runners/`

**user**:
The person. By day they work with the main agent on specs and tickets; they are the only reader of a `ready-for-human` ticket; `needs-triage` and `needs-info` wait on them; they are told when the night is over.
_Avoid_: human (for this), maintainer (in this repository's text), reporter (in this repository's text), 用户 (as a term)
_Home_: `docs/agents/triage-labels.md`

**subagent**:
An agent started inside another agent's session, holding its own context and answering back into that session. The toolbox ships no subagent definitions and installs nothing into any host's `agents/` directory: a skill that needs one asks for the host's own general-purpose subagent, which runs on the model of the session that starts it and has no live-table row. Results that must be written back to the ticket, read by another role, and openable by a person run as a session a runner starts (`dispatch.sh start`) instead; work that is only an internal split of the current step runs as a subagent. The three code-review axis subagents are subagents of the reviewer session; the reviewer and the verifier themselves are sessions the worker starts, not its subagents.
_Avoid_: sub-agent, background agent, seat, 子代理 (as a term), native subagent, assembled subagent file
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**caller**:
Seen from inside a skill or subagent, the agent that invoked it and composed its packet. A caller names the skill and what it wants done, never an install path.
_Avoid_: 调用方 (for this)
_Home_: `AGENTS.md`

### Places

**MMW**:
This toolbox: skills and subagents the user shares across hosts, repositories, and machines. Only `mmw-v2/` is live; `archive/` is the previous generation, frozen; `deprecated/` holds what v2 itself retired.
_Admitted_: the toolbox
_Avoid_: 工具箱, this repository (as a name), 活层, live layer
_Home_: `AGENTS.md`

**consuming repository**:
The outside repository where real tickets are run, as distinct from the toolbox. It must hold a `DESIGN.md` before UI refinement; the live table is never placed in it.
_Avoid_: consumer repo, 消费仓库, the project (for this), the repo (for this)
_Home_: `AGENTS.md`

**repository root**:
`git rev-parse --show-toplevel`: the fixed working directory of every `CHECK:`, and where `CONTEXT.md` and `AGENTS.md` live.
_Avoid_: repo root, 仓库根
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**subtree**:
How an upstream repository is carried inside this one: `git subtree pull --prefix … --squash`. `mmw-v2/upstream/` is `mattpocock/skills`; `mmw-v2/upstream-diagram-design/` is `cathrynlavery/diagram-design`. A change to a skill inside a subtree requires a merge-note. `gate-check/` is not a subtree; its provenance is `UPSTREAM.md`.
_Home_: `mmw-v2/merge-notes/README.md`

**upstream**:
The source project of a subtree. Its own `AGENTS.md`, `CLAUDE.md`, and `CONTEXT.md` are left untouched; any passage no merge-note covers is taken as upstream wrote it.
_Avoid_: 上游票号 (that is a blocker)
_Home_: `mmw-v2/merge-notes/README.md`

**unlazy**:
The repository `gate-check/` was copied from (`https://github.com/Leonxlnx/unlazy`, commit `da0b00a3`, MIT). It is not a subtree; the copy is recorded in `UPSTREAM.md`.
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`

**source directory**:
One of the three directories in this repository a host's skill symlink points straight at (`mmw-v2/skills/`, `mmw-v2/upstream/skills/`, `mmw-v2/upstream-diagram-design/skills/`), so an edit takes effect on the next call. `install.sh` knows a link is its own because `readlink` lands inside one of them.
_Avoid_: 源目录 (as a term; the merge-note field `源目录：` is a literal), 仓库源目录
_Home_: `mmw-v2/install.sh`

**`~/.agents/skills`**:
The host-neutral install location `install.sh` creates on every machine; Codex, Cursor, Grok, and Pi scan it. `~/.claude/skills` is the second copy, because Claude Code scans only that. Both hold symlinks straight to the source directory. The four per-host locations `~/.codex/skills`, `~/.pi/agent/skills`, `~/.cursor/skills`, `~/.grok/skills` are retired.
_Avoid_: 通用位置, 中立目录, 用户级目录
_Home_: `docs/adr/0006-skills-install-to-neutral-dir.md`

**symlink**:
What `install.sh` makes: skills into the two install locations, `~/.claude/CLAUDE.md` to `prompt/shared.md`, and `~/.local/bin/paseo` to the Paseo CLI. `hook.py` is not linked anywhere: each host's configuration names it at its path under `~/.agents/skills`. A symlink is not a copy — the host reads the repository file — and whichever checkout runs `install.sh` takes over the batch.
_Avoid_: agent detection rule
_Home_: `mmw-v2/install.sh`

**stale link**:
A symlink that points back into this repository but is not on the list, or a last-generation link left in a retired location. `install.sh --check` prints `残留` and returns 1; `install.sh` removes it.
_Avoid_: 残留 (as a term; the printed prefix is a literal)
_Home_: `mmw-v2/install.sh`

**retired**:
The state of a skill or subagent moved to `deprecated/` (unchanged, not treated as fact), and of an install location that is no longer a target though its host still scans it. The retired locations are the four per-host `skills/` directories and every host's `agents/` directory, including `~/.grok/roles/`. `install.sh` prints `退役` when it clears its own links from one.
_Avoid_: 退役 (as a term; the printed prefix is a literal)
_Home_: `AGENTS.md`

**issue tracker**:
GitHub Issues for this repository, every operation through `gh`. It is the only store of fact and state: parent–child relations, blocking links, the frontier, and claims exist only here. Its operations — Create, Read, List, Comment, Apply and remove labels, Close, Re-parent, Transfer, Read a PR, List external PRs, Claim, Resolve — are each one `gh` command in `docs/agents/issue-tracker.md`; `publish to the issue tracker` means create a GitHub issue; `PRs as a request surface` is `no`.
_Admitted_: the tracker
_Avoid_: backlog (for this), 真 tracker, GitHub Issues (as a term)
_Home_: `docs/agents/issue-tracker.md`

**`gh`**:
The CLI every issue-tracker operation goes through. `CLICOLOR` and `CLICOLOR_FORCE` are unset before every call.
_Home_: `docs/agents/issue-tracker.md`

**Paseo**:
One of the three runners, a daemon whose sessions are Paseo agents; its CLI is `paseo`. Its adapter starts each session in one call, in the directory it is given, never in a Paseo workspace. What sets it apart from the other two: a live-table row is resolved against its own provider catalog rather than the host CLI's, and it is the one runner a script asks directly rather than through the adapter — `check` asks it whether each host is available when it is tonight's runner.
_Avoid_: terminal multiplexer
_Home_: `mmw-v2/skills/dispatch/scripts/runners/paseo.sh`

**Paseo agent**:
A session Paseo runs. It has an id (the `session` of a started event whose `runner` is `paseo`, when `start` started it), a title (`#<n> worker`, `#<n> reviewer`, or `#<n> verifier`), a cwd whose basename is the worktree slug, and a `status`, which the Paseo adapter reads to answer `liveness`.
_Home_: `mmw-v2/skills/dispatch/scripts/runners/paseo.sh`

**Paseo subagent**:
A Paseo agent started from inside another Paseo agent, which Paseo records as its parent (`ParentAgentId`). A reviewer or verifier the worker starts is one only when both run on Paseo. Nothing in the pipeline relies on the parent link: a result wakes the session its **recipient** rule names, whichever runner either runs on, and landing stops every session the ticket's started events name, one by one.
_Home_: `mmw-v2/skills/dispatch/scripts/runners/paseo.sh`

**workspace**:
The per-ticket unit `dispatch.sh` opens and archives: the worktree `<repository root>/.worktrees/issue-<n>` together with every session the ticket's started events name. `start` opens it with git (`git worktree add`, or reuses the one standing), has tonight's runner start a session in it by absolute path, and writes that path into the started event, so no runner is ever asked to find it. Archiving it — `advance` after merging that ticket's branch, `land`, `retract` — gives back the product slot its worktree holds, if it holds one, stops each of those sessions through the runner its event names, and removes the worktree with `git worktree remove --force`. No runner creates or removes it.
_Avoid_: 工作区 (for the git sense, that is a worktree), pane, monitor tab, Herdr workspace, Paseo workspace
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**Agent profile**:
A hand-written entry in `~/.paseo/config.json` under `daemon.agentProfiles`. It is not MMW config: `install.sh` does not write these from the live table. Notes containing `from models.md` are leftover generated profiles — `--check` reports `残留`, install drops them. Hand-written profiles are left alone.
_Home_: `mmw-v2/install.sh`

**finish notification**:
A `<paseo-system>` block Paseo delivers to the session that started an agent through Paseo's own MCP tools: its first sentence is `Agent <id> (<title>) finished.` or `errored.` or `was closed.` or `needs permission.`, and it may carry an `<agent-response>` of the agent's last reply. `start` starts every session through the runner adapter, never through those tools, so nothing in the pipeline waits on one: a result is an event on the ticket, and the **relay** turns it into a **wake**.
_Avoid_: wakeup loop, re-prompt, STOPPED, TIME LIMIT, `mmw board:` line, pane event, turn, turn.py, board log
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**wake**:
What the **relay** sends a **recipient** when an event it waits on lands on a ticket: `#<n> <event>`, the ticket number and the event's name and nothing else, through the `send` of the runner that runs the recipient (`relay.recovered since <time>` for the one row about the relay itself). A worker is woken for `reviewer.reported`, `verifier.passed` and `verifier.failed`, for `reviewer.lost` and `verifier.lost`, and with `worker.queued` when its ticket waits for a product slot and one is given back; the main agent of the ticket's watch for `ticket.passed`, `ticket.returned`, `ticket.refused`, `child.opened` of kind `fault` or `decision`, `worker.lost` and `relay.recovered`. What happened is read on the ticket; the wake only says where to look. It can cut short a command the recipient was running, so that command is run again first; then the recipient reads the event, acts, and acks the wake. No script sends one: `verify-ticket.py` posts events and tells nobody, and no runner's own notification is relied on. A `watchdog:` line is not a wake: the **watchdog** sends it itself, and it is not acked.
_Admitted_: wake-up
_Avoid_: ticket message, closeout notification, 通知 (as a term)
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**worktree**:
The per-ticket git worktree of a workspace, `<main checkout>/.worktrees/issue-<n>`, on the ticket branch `issue-<n>`. A directory `issue-<n>` on any other branch is not this workspace. `dispatch.sh` creates and removes it with git; no runner name is in the path, and a runner is only told the absolute path. The reviewer and verifier run inside it.
_Avoid_: 工作区, checkout (when this is meant), ~/.mmw/worktrees
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**ticket branch**:
The branch `issue-<n>`, shared through `origin/issue-<n>`; `dispatch.sh` pushes it and never force-pushes it. `--preflight` refuses when the session is not on it.
_Admitted_: `issue-<n>`
_Avoid_: branch (bare), 分支名 (as a term)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**base commit**:
The commit recorded in `git config branch.issue-<n>.mmw-base` when the workspace was created: HEAD at a new `branch-off`, or — for a ticket branch that already existed with no record — its merge base with HEAD at that dispatch. `start` reads it and writes it into the review dispatch line and into the `base` field of every started event; it is where code review's diff starts (`git diff <base-commit>...HEAD`, three dots), and where the first-parent chain behind `Outside Owns:` begins. Written `<base-commit>` as a placeholder.
_Avoid_: base-commit (in prose), 起点 commit, cut point, 切点
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**base branch**:
The branch on `origin` a night's tickets merge into; the copy at `origin/<base branch>` is authoritative and a local branch of the same name is a cache. The main agent opens the night on it, and `spec.opened` and `worker.started` name it in `into`.
_Avoid_: main branch, 基线分支, main (as a name)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**Claude Design**:
The design tool whose downloaded project is the handoff package and the baseline side of a parity run. Its page format is Design Components (`<x-dc>`, helmet, `sc-if` / `sc-for`, `data-props`, `dc-import`); its runtime is `support.js`.
_Home_: `mmw-v2/skills/claude-design-blocks/references/porting.md`

**component**:
A root-level `<name>.dc.html` page in a Claude Design project that exposes a `scene` prop, one value per state. A handoff package carries one. Its helmet pins the page root `#dc-root`, which is where the baseline side is screenshotted from. A wrapper page imports it with `<dc-import name="…" scene="…">`, whose `scene` attribute pins one scene. The `component` column of a screen contract's `pages` is a different thing — the product component that owns that page — and is defined in `mmw-v2/skills/align-screens/references/contract-format.md`.
_Avoid_: design component, scenario, scenario 属性, 状态开关
_Home_: `mmw-v2/skills/claude-design-blocks/references/porting.md`

**handoff package**:
A Claude Design project downloaded into the prototype leaf directory `prototypes/<task>/<issue>/UI/`: the six things the driver renders — the component's `.dc.html`, `styles/`, `data/`, `support.js`, `scenes.json`, and `vendor/` holding the three scripts `support.js` loads — plus the `README.md` a spec and its tickets take exact values, verbatim copy and `viewports` from. The screen contract's `baselines.look` names it; `story-parity.py` and `extract_skeleton.py` render it; the Spec axis does not open it; it supersedes the winning variant under `## Read first`; once downloaded it is a contract, copied verbatim, not a reference. The target trees are its derived view.
_Avoid_: 交接包, 开发交接包, 基线目录, UI 基线
_Home_: `mmw-v2/skills/drive-target/references/story-parity.md`

**scene**:
One entry of `scenes.json`: `name`, `page` (the `.dc.html` it pins), `props` (the prop set that puts the design page into that state), and `data` (**scene data**). The screen contract declares every scene once under `scenes`, with its page. The product story is addressed by `?page=&scene=`; the view does not answer a query parameter from fixtures of its own. Each scene gets its own screenshot and tree per viewport. The name may not contain `/`, because its wrapper page is `/__parity-<name>.dc.html`. In Claude Design a scene is one value of a component's `scene` prop, switched from the Tweaks panel; the word is the same on both sides, and there is no second word for it.
_Avoid_: 场景 (when a scene is meant), 场景列表, scenario, 状态
_Home_: `mmw-v2/skills/claude-design-blocks/references/handoff.md`

**`DESIGN.md`**:
The consuming repository's design-system file. When it is missing, the `create-design-md` skill (`ibelick/ui-skills@create-design-md`, installed with the skills CLI) writes one; it is uploaded once per project as the Claude Design design system.
_Home_: `mmw-v2/skills/claude-design-blocks/references/porting.md`

**prototype**:
Code that answers one design question, kept in the repository under `prototypes/<task>/<issue>/<UI|LOGIC|EXP>/` and iterated as the answer sharpens; the real implementation is written with it as reference. Its question and verdict live in the leaf `README.md`; it has no tests. A UI prototype is several structurally different **variants** (default three, at most five) on one real route, switched by `?variant=`; the user picks the winner, `?variant=<winner>`. The mount point, symlink, and switch that let variants render inside the real app are **scaffolding**, taken down in step 6 of `prototype/UI.md`; a **prototype route** is one created for the variants and deleted when the winner is promoted. A prototype's chosen artifact — the winning variant, the validated logic module, an experiment's Reusable parts with its Conclusion — is a baseline source.
_Avoid_: throwaway (for this), 一次性分支, 原型 (as a term), 研究件, UI variation (in this repository's text), throwaway route, 挂载点连同软链
_Home_: `mmw-v2/upstream/skills/engineering/prototype/SKILL.md`

**leaf directory**:
`prototypes/<task>/<issue>/<UI|LOGIC|EXP>/`, one per prototype kind; `<issue>` is the ticket number. The handoff package and `scenes.json` live in the `UI/` one. Once folded in, it is the only home a prototype has. Its `README.md` is the **leaf README.md**, read to its verdict as a `## Read first` item.
_Avoid_: 叶子目录, the leaf (bare)
_Home_: `mmw-v2/upstream/skills/engineering/prototype/SKILL.md`

**`docs/agents/`**:
The three files `setup-matt-pocock-skills` seeds once: `issue-tracker.md`, `triage-labels.md`, `domain.md`. `triage-labels.md`'s `## What carries a label here` section is this repository's own and a re-run would overwrite it. `AGENTS.md`'s `## Domain docs` block points at `domain.md`; this repository is a single context, `CONTEXT.md` plus `docs/adr/`.
_Avoid_: tracker 配置, 单 context (as a term)
_Home_: `mmw-v2/merge-notes/setup-matt-pocock-skills.md`

**`CONTEXT.md`**:
This file: the vocabulary of the pipeline, one namespace. `mmw-v2/upstream/CONTEXT.md` is upstream's own. `domain-modeling` writes it; a worker reads it last before writing code. It doubles as the interface record — command signatures, constant tables, fixed output shapes — so a definition may run longer than two sentences. The rule: use the term as defined here and do not drift to a word its `_Avoid_` line lists.
_Avoid_: 词表, glossary, domain glossary, 接口契约
_Home_: `docs/agents/domain.md`

**`AGENTS.md`**:
A repository's agent instruction file, root plus nested pairs; this repository's carries `## Agent skills` and `## Domain docs`. `CLAUDE.md` beside it holds only the line `@AGENTS.md` and other `@` imports.
_Avoid_: bridge (for this)
_Home_: `mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/SKILL.md`

### Specs and tickets

**issue**:
A GitHub issue, the issue tracker's unit. In this pipeline it is a spec, a ticket, a sub-issue, a decision ticket, a map, or an issue from outside that triage handles. Its **ticket state** is `OPEN` or `CLOSED`.
_Home_: `docs/agents/issue-tracker.md`

**spec**:
A top-level issue that holds a batch of tickets. It is a container, not work, so it carries no queue label; its one label is the layer label `mmw:spec`, which `to-spec` puts on when it publishes it. `to-spec` writes it from the conversation, a cleared map, or an agent brief, in the `<spec-template>` shape: `## Problem Statement`, `## Solution`, `## User Stories`, `## Implementation Decisions`, `## Testing Decisions`, `## Out of Scope`, `## Sources`, `## Further Notes`. Decisions that share one seam belong in one spec. A worker reads only the subsections its ticket's `## Parent` names, plus `## Testing Decisions` and `## Out of Scope`. A section of a published spec is changed in place by `to-spec`'s step for revising a published spec — the body stays the clean current version, what changed and why goes in one comment — so the number and every ticket's `## Parent` stay valid. The night runs on it: `run <spec>`, `advance <spec>`.
_Admitted_: spec issue
_Avoid_: 父票, spec 票, 规格
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Implementation Decisions`**:
The spec section of decisions made, in numbered subsections `### 1.` … that tickets point at by number in `## Parent`. Every decision names its source — a decision ticket number, an ADR, a research path — or says `this spec's decision`. It names no implementation file paths.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Testing Decisions`**:
The spec section whose first sentence says in plain words where a test looks at the result (a browser page, an HTTP endpoint, or a function call) and whose second names the seam and which external seams may be stubbed; then, per test layer, its directory and the precedent to copy; then **How a test arrives at a state** — the mechanism that puts the system into each state the behaviour turns on, which must be named here and owned by some ticket's `## Owns`, else `to-tickets` cuts a `reach` ticket for it; last, the commands to run before committing. `CHECK:`, `EXPECT:`, and the ticket's `## Seam` are derived from it; a review finding that touches it is in-ticket.
_Avoid_: 测试怎么到达状态
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Out of Scope`**:
The spec section of what is not being done; read by the worker and the Spec axis along `## Parent`, and the sharpest source of a `Scope creep` finding, which is in-ticket. (A wayfinder map's **Out of scope** section is a different literal, carried into the spec unchanged.)
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Sources`**:
The spec section of links to the first-hand material it was built from, one line per kind in nine fixed kinds — map, decision tickets, Upstream specs, ADRs, research files, prototypes, Domain docs, Evidence, Test rules — `none` when a kind is empty. `## Read first` picks per ticket from here.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**seam**:
The place a test observes: the public boundary you test at. `to-spec` chooses it without asking the user; it is the subject of `## Testing Decisions`'s second sentence and of a ticket's `## Seam`. **External seams** are the third-party ones that may be stubbed.
_Avoid_: boundary (for a seam)
_Home_: `mmw-v2/upstream/skills/engineering/tdd/SKILL.md`

**precedent**:
The similar existing test `## Testing Decisions` names per test layer. It is copied into the ticket's `## Seam`; the ticket writer opens it to copy its framework and single-file invocation into `CHECK:` and runs it once to take the `EXPECT:` marker.
_Admitted_: the precedent to copy
_Avoid_: prior art, 先例, the precedent it names
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**test layer**:
The layer a feature's tests land in — named per layer with its directory and precedent in `## Testing Decisions` and copied into `## Seam`. The toolbox's own tests have five layers: **structural check** (`install.sh --check`), **own-script layer** (this repository's scripts against fixed samples, entry `tests/run.sh` per skill), **vendored-script layer** (the tests that came with copied upstream scripts), **skill-behaviour layer** (run the skill for real on a throwaway ticket inside a worktree and check what appears on the ticket), and **real ticket** (one real ticket carried from writing to closing; nothing merges to the base branch until it passes).
_Avoid_: 测试层, 结构核对, 自写脚本层, vendor 脚本层, 技能行为层, 真票
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**ticket**:
A GitHub issue created as a native sub-issue of its spec (`gh issue create --parent <spec>`, or attached through the `sub_issues` API), in the `<issue-template>` shape. It is a tracer-bullet vertical slice with its blocking links; the only place fact and state are kept; the worker's only input, read at five moments; it must have an issue number. At publication it takes one of two shapes: an agent ticket (labelled `ready-for-agent` plus a worker grade) or the separate `ready-for-human` ticket. A ticket this repository plans for itself carries a state role only. Its **ticket body** is the sections, not edited once the batch has been reported to the user as published — the read-back step, which fixes tickets and runs `--lint` again, comes before that report; its **ticket number** is `<n>` — digits only. A **batch** is the tickets under one spec, published together and worked in one night.
_Admitted_: issue (when naming the GitHub object)
_Avoid_: 票 (as a term), child ticket, slice (as a name), 本批, 票号, body (bare)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**vertical slice**:
The rule that a ticket cuts a narrow but complete path through every layer, by feature and never front end against back end, demoable on its own; its title and `## What to build` describe the same slice. There are UI acceptance criteria but never a UI ticket. Wide refactors are the exception.
_Admitted_: tracer-bullet
_Avoid_: 纵切, slice (as a name)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`<issue-template>`**:
The ticket template in `to-tickets/SKILL.md`: `## Parent`, `## What to build`, `## Read first`, `## Seam`, `## Owns`, `## Acceptance criteria`. Sections read by position downstream keep these exact headings; renaming one means changing `implement` too.
_Avoid_: 六节, 七节, 八节 (as names)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Parent`**:
The route from the ticket to its spec: `#<spec>, Implementation Decisions section <n>`. One of the five things a `ready-for-human` ticket holds.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## What to build`**:
The end-to-end behaviour this ticket makes work, from the user's point of view, in numbered points each with the test that decides it and the reason it is there; a choice the user settled in the `to-tickets` quiz is a point of its own. It describes the same slice as the title (checked at read-back and after claiming) and is never simplified away.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Read first`**:
The sources the ticket's spec subsections cite, `None` when there are none. Each item is read to its conclusion before work: a research file's last section, an ADR's decision (its `# ` heading and the prose under it), a handoff package, a prototype's leaf README.md to its verdict. Items that record a settled conclusion are baselines. It is re-read at the Audit, and searched before a helper is written.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**baseline**:
An item under `## Read first` that records a settled conclusion: a decision ticket's resolution, an ADR's decision (its `# ` heading and the prose under it), a research file's conclusion, a handoff package, a prototype's chosen artifact. To the worker it is a contract, not a reference; a handoff package is copied verbatim, a prototype is rewritten to production standard. The Spec axis reads the baselines against the diff, and a deviation is `Built wrong`. The screen contract's `baselines.look` names the handoff package directory, and the story judge's output word for that side is `baseline`.
_Avoid_: 基线 (as a term), reference (when this is meant), `baseline` (as a child kind; a baseline that does not hold is a `contract` child)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**contract**:
The bond between a worker and every baseline in `## Read first`, in three clauses: copy exact values, wording, states, and interface shapes; never deviate quietly; never bend a baseline, a harness, or a test. **The baseline is the contract** is the first of the writing rules. **The contract does not fit** is the case where a baseline lacks a state, a field, an interaction, or a case the work needs, or two baselines conflict: keep going, open a `contract` child under the ticket (`--sub-issue contract`), add nothing quietly.
_Avoid_: 契约 (as a term), 安装契约, 接口契约, 基线是契约, 契约装不下, 基线装不下
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`## Seam`**:
Where this ticket is verified: the test layer and directory copied from `## Testing Decisions`, the precedent to copy, and how a test arrives at the state. Present and non-empty on every agent ticket; when a ticket lacks it, the worker derives it from `## Testing Decisions` and comments it on the ticket before writing code.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Owns`**:
The repository-relative paths this ticket may write, one per line — where you may write, not where the code is. It includes the Seam's test directory or file; a path the ticket creates is marked `(new)`; no absolute path, `..`, or bare `**`. Two tickets on one frontier may not overlap; where they would, a blocking link is added on the tracker. A ticket that has a directory to itself writes a **directory glob**; several tickets dividing one directory go down to file level. The **Owns check** at start of work confirms every glob matches or is `(new)` (an older ticket derives one from its Seam). A ticket that deletes or renames a public name — a file, a script, a contract field, a criterion word — takes every `grep` hit for that name into its own Owns, or opens a cleanup ticket `Blocked by` the ticket that owns a stale reference. The **Owns two grades** rule handles a file outside Owns: change it and record it under `Outside Owns:` when a criterion cannot pass otherwise; leave it and open a `deferred` child (`--sub-issue deferred`) when the change is merely convenient.
_Avoid_: 目录 glob, Owns 核对, Owns 两档
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Acceptance criteria`**:
The ticket section holding the acceptance criteria, one after another. A `ready-for-human` ticket has none.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**Blocked by**:
One of the five things a `ready-for-human` ticket holds: the ticket that produces the thing it waits on. An agent ticket carries no such item; its blocking lives on the tracker's native blocking links alone.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**acceptance criterion**:
One standard on a ticket, decided by one command — a judgement that is not decided by a command is not an acceptance criterion. Four lines: `- [ ] AC<n>:`, `CHECK:`, `EXPECT:`, `EVIDENCE: pending`, with an optional `CWD:`. Three writing rules: externally observable behaviour, exact values copied from the spec or a prototype artifact, one assertion each. Numbered when the ticket is written and never renumbered, because the ledger cites by number. `--lint` checks how it is written, `verify-ticket.py <n>` runs it, the verifier re-runs it; a reviewer may not add criteria the ticket lacks.
_Admitted_: criterion
_Avoid_: AC (in prose), 标准 (as a term), 验收标准, gate (for a criterion), oracle, 判据 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`CHECK:`**:
The shell command that decides a criterion. It runs in its own shell with the working directory at the repository root (or `CWD:`); a multi-line command is written only as a fenced block directly under it. It is the one line in the pipeline a shell runs with no agent in between, so the program that runs it supplies its environment: `verify-ticket.py` puts every `--tools` directory on that shell's `PATH` and sets `MMW_TICKET` to the ticket number, and the line names a judge by its bare name and carries no install location. Its text comes from the precedent named in `## Testing Decisions`. A command may write `$MMW_TICKET` for the ticket number it is running against.
_Avoid_: check command, the check (for this)
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**`EXPECT:`**:
The string, or `/…/flags` regex, the `CHECK:` output must contain. It is written to the **success-only marker** rule: the line the precedent prints only when it passed, copied whole after running it once — never `ok`, `passed`, or `done` on its own. `gate-lint` reports a weak one as `weak-expect`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`EVIDENCE:`**:
The fourth line: `pending` until the criterion has run, then the one line of fact gate-check writes in the fixed shape `exit=…; shell=…; cwd=…; path=…; EXPECT=matched; output-sha256=…; output-bytes=…` (the **EVIDENCE structured line**). A ticked criterion still reading `pending` is unmet.
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs`

**`CWD:`**:
The optional fifth line: the working directory `CHECK:` runs in. gate-check calls these indented lines the criterion's **attributes**.
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/lib/gates.mjs`

**`TIMEOUT:`**:
The optional attribute line `TIMEOUT: <seconds>` under a criterion: how long its `CHECK:` may run. `verify-ticket.py` reads every `TIMEOUT:` off the ticket body on every run, worker's and verifier's alike, and hands gate-check the largest of `DEFAULT_TIMEOUT` (600), those lines, and `--timeout`; it raises the limit and never lowers it, and is kept out of the ledger. `--lint` reports one that is not a positive whole number as `ERROR … [bad-timeout]`.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**fenced block**:
The only way to write a multi-line `CHECK:`: a code fence directly under it is the command; every other fence in the ticket is skipped; a flush-left continuation line with no fence is a parse error.
_Avoid_: fenced check, fenced code block, 代码块围栏, 围栏
_Home_: `mmw-v2/skills/verify-ticket/references/running-criteria.md`

**the five questions**:
What the ticket writer asks, in order, of anything there is to say about the work, stopping at the first yes: is it an acceptance criterion (decided by a command)? a code-review judgement (written into the spec's `## Implementation Decisions` subsection the ticket names, where the Spec axis reads it as in-ticket)? a person's `reaction`? a `reach`? or a choice — asked of the user in the quiz, the answer written into the ticket's `## What to build`.
_Avoid_: 五问, 五问判定树
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**both conditions**:
What it means for a criterion to pass: the `CHECK:` exits 0 and its output matches `EXPECT:`. gate-check applies it.
_Avoid_: 双条件, the double condition
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`

**`met`, `unmet`, `abandoned`**:
The three states of a criterion: **met** is ticked with real evidence; **unmet** is not ticked, or ticked with `EVIDENCE: pending`; **abandoned** carries an `ABANDON:` line. **ticked** is the checkbox state in the ledger; `--reverify` re-runs ticked criteria too. A criterion is **runnable** when both `CHECK:` and `EXPECT:` are non-blank.
_Avoid_: 勾 (as a term)
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**round**:
One fix-and-rerun pass on one criterion. How many a criterion gets is the worker's judgement, and `--closeout` counts none: the reason on the `ABANDON:` line says what was tried. One round of code review and the night's `reverify` are always written in full.
_Avoid_: 轮 (as a term), 三轮上限
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`ABANDON:`**:
The line `ABANDON: AC<n> <kind> <reason>` a worker — never the verifier — writes under a criterion it gives up on. The kinds: **`failed`** — it ran and did not pass (after the rounds the worker judged worth spending, or still failing after the review fix or the verifier's report), its reason saying what each round tried; **`stuck`** — it will not start or cannot be done within the ticket (a `CHECK:` that will not run, a missing credential or device, out of reach within the scope), its reason listing the routes tried or pointing at the sub-issue; neither is held to a round count, and the two are told apart for whoever reads the ticket in the morning; **`decision`** — a person has to settle one sentence, a `decision` child is opened under the ticket (`--sub-issue decision`), and it is the only kind that still lets the ticket close `ALL MET`. `failed` and `stuck` force `HANDOFF REQUIRED`.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

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
A GitHub label on an issue, from one of three sets that each answer one question and never stand in for each other: a **layer label** says which layer of the tree the issue is, a triage label which queue it is in, a worker-grade label which worker row starts it. `wayfinder:*` are the wayfinder skill's own, and `bug` and `enhancement` belong only to issues from outside. A spec carries its layer label and no other. On a ticket in the agent queue only `--closeout` changes a queue label; the hook refuses any other command that would.
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
The `ready-for-human` kind where the property asserted is a person's reaction: the person is the measuring instrument, and the ticket cannot be retired.
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
Wayfinder's single issue labelled `wayfinder:map` and the layer label `mmw:map`, the canonical index: Destination, Notes, Decisions so far, Not yet specified (the fog), Out of scope, `## Specs`. Its children are decision tickets; it is cleared when the frontier and Not yet specified are both empty, and never closed. One of the nine `## Sources` kinds.
_Admitted_: wayfinder map (in `## Sources`)
_Avoid_: shared map (in this repository's text), 地图 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**agent brief**:
The record `triage` posts on an issue at the evaluation stage — an investigation record, not a work order — ending with the disclaimer line `*This was generated by AI during triage.*`.
_Avoid_: brief (bare), 工单
_Home_: `mmw-v2/upstream/skills/engineering/triage/AGENT-BRIEF.md`

### Comments on the ticket

**ticket comment**:
One comment a script or an agent leaves on the ticket. Every one a script leaves is an **event**, and an event block is the only part of any comment a program reads: a run of the criteria, the files another ticket changed, a wait for a product slot and a failed repository check are events like the rest. A comment an agent types — a `## Seam` it derived, a note on a wrong `CHECK:` — is prose, which no program reads. The ticket's comments are its only run state.
_Avoid_: 票评论, COMMENT (as a kind label), `self-run`, `reverify`, `TOUCHED BY`, `CHECKS FAILED` (each as a comment found by its first line)
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**event**:
One comment that records one thing that happened, in two parts: a first line and any prose after it, for a person, and a trailing `<!-- mmw {...} -->` block — one line of JSON, invisible on GitHub — which is the whole of what a program reads. Its name is `subject.verb`: a subject from `spec`, `ticket`, `worker`, `reviewer`, `verifier`, `child`, a verb in the past tense, lower case, and never a value inside the name — ticket numbers, commits, hosts and models are fields of the payload. Every payload carries `v`, `event`, `stage`, `actor`, `spec`, `ticket` and `at`; which further fields each event requires, and which take a closed set of values, is the table `EVENTS`. Every event is posted by a script — `verify-ticket.py`, or `dispatch.sh` through `events.py emit` — and never typed by a model, so a `VERDICT` written with `gh issue comment` carries no event and counts for nothing. Prose that quotes an event has its opener turned into visible text (`neutralise`), so a comment carries no block but its own.
_Admitted_: event block (the trailing block alone)
_Avoid_: protocol comment, status word, marker line
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**fold**:
A ticket's state, computed and stored nowhere: the issue's comments read in comment-id order and their events replayed from an empty state. The order is by id, never by timestamp, because two comments written in the same second carry the same one; an edited comment counts in its newest version. The replay starts from empty every time and never updates a state it computed before, because state goes backwards — `ticket.regressed` takes back a pass and a landing, `ticket.released` a claim, `worker.retracted` a start — and a replay needs no inverse for any of them. A comment with no block is prose and changes nothing, whatever its first line says. `events.py fold <issue>` prints it; `status.py`, `dispatch.sh`, `verify-ticket.py` and the relay read a ticket's events through `events.py` and nowhere else.
_Avoid_: phase inference, state file, incremental state
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**held**:
What the fold says of a ticket an agent may still be working: it stays off the frontier and `advance` does not give its claim back. A ticket is held from its `ticket.claimed` or any `worker.started`, `reviewer.started` or `verifier.started` until an event ends the hold. `ticket.landed`, `ticket.returned`, `ticket.released` and `spec.suspended` end every hold on it; `worker.retracted`, `worker.lost`, `worker.replaced`, `reviewer.lost`, `verifier.lost` and a `ticket.refused` that names its session end the one session they name, matched by its (runner, session) pair and never by the id alone, since two runners can hand out the same id; a retraction also ends a claim no started session has taken over; `worker.resumed` makes the session it names live again. A result ends the hold of the session that produced it: `reviewer.reported` that reviewer's, `verifier.passed` or `verifier.failed` that verifier's (the one it names, else the newest live one of that kind), so a finished reviewer never keeps a ticket whose worker is gone. `ticket.passed` ends none — the close after a pass can fail and leave the worker retrying — and no label ends one. It is the same answer whichever runner and machine the worker runs on. A worker that died with nothing ending its hold keeps its ticket held until the **watchdog** writes `worker.lost` — once the worker's own runner says its session has stopped — or `retract` writes `worker.retracted`; one whose runner cannot say stays held; a claim that no event ever showed held — one assigned by hand, say — is never given back by `advance`, since nothing shows its worker gone. A hold is not a product slot, which a worktree keeps until its ticket's work ends, past a replaced or lost worker (see **lease**).
_Admitted_: hold (the noun)
_Avoid_: live worker (as what keeps a ticket off the frontier), occupied, 占用 (as a term)
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**unreadable event**:
A comment carrying an `<!-- mmw` block the fold cannot read: never closed, two blocks in one comment, not JSON, a version other than 1, no event name, or a payload `EVENTS` refuses. It is never skipped as prose: the fold lists it under `unreadable`, and every command that decides from the fold refuses to decide about that ticket until a person fixes the comment — `events.py session`, `sessions` and `result` exit 3, `wait`, `resume` and `retract` refuse, `advance` neither merges, releases nor dispatches the ticket, `suspend` leaves it as it was, `--closeout` refuses, and `status` notes `events unreadable: …`.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**landed**:
A ticket whose branch is in the base branch, recorded by the `ticket.landed` event `advance` or `land` writes once the merge is in `HEAD`, or once it finds the branch already there. It is not **closed**: `--closeout` closes the ticket on the tracker together with `ticket.passed`, before anything is merged, so a ticket is closed and not landed until the next `advance` or `land`. A blocked ticket is let go when its blocker has landed, because the blocked ticket's worktree is cut from the base branch and an unmerged blocker left nothing there; a blocker that closed without a `ticket.passed` lets go on closing, since nothing of it will ever land. That rule is `events.blocker_hold`, the one answer the frontier, `start`, `adopt` and `--preflight` all give. `reverify` re-runs landed tickets only, and `ticket.regressed` takes back both the pass and the landing.
_Avoid_: closed (for this), merged (as the state of a ticket), done
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**first line**:
The first line of a ticket comment. On an event it is prose for a person, worded however its writer likes, and no program reads it: rewording it breaks nothing, and every comment a script posts is an event. Two first lines are a script's input before they are posted: `--closeout` reads a draft's `ALL MET` or `HANDOFF REQUIRED:` to post it as `ticket.passed` or `ticket.returned`, and `--review` reads a report's `REVIEW <base commit>..<HEAD commit>` for the event's two commits. `--sub-issue` takes a child's title from the first line of its file. A disclaimer goes last.
_Avoid_: 首行 (as a term), protocol slot, 协议位, status word, slot (bare — see **slot**)
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`worker.started`, `reviewer.started`, `verifier.started`**:
The event `dispatch.sh start` posts on the ticket once the runner has started the session: `session` (that runner's own id for it), `runner`, `host`, `model`, `effort` (`—` when the host takes none), `grade`, `worktree` (an absolute path), `branch` and `base`. It records no product slot: a worker takes one at its first run that needs the product, and that run's `ticket.checked` names it. It is the only record of the session: `resume`, `wait`, `retract`, `land` and `suspend` find the session in the newest such event of its kind and ask the runner it names, and no other, so every machine that reads the ticket gets the same answer. A session whose event cannot be written is stopped again and the start refused, so none runs where nothing can find it. Each one begins a hold.
_Admitted_: started event (any of the three), `*.started`
_Avoid_: RUNNER line, runner line
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`ticket.claimed`, `ticket.refused`**:
The two events `--preflight` posts, one or the other. `ticket.claimed` follows the claim and begins a hold; the assignee is the claim, so a claim whose event could not be written still stands, and stderr says so. `ticket.refused` carries the first refusal's `reason` — `wrong-branch`, `dirty-tree`, `not-open`, `not-ready`, `blocked`, `claimed-by-other` — and its first line is the sentence `NOT_READY: <reason>` that `--preflight` also prints; exit 2, and the worker stops.
_Avoid_: NOT_READY (as the name of the refusal; `NOT_READY: …` is its first line and its printed text)
_Home_: `mmw-v2/skills/verify-ticket/references/claiming.md`

**`ticket.passed`, `ticket.returned`**:
The two events `--closeout` posts a closing comment as, each after the change it announces: `ticket.passed` for an accepted `ALL MET` draft, once the ticket is closed; `ticket.returned` for a `HANDOFF REQUIRED` draft, carrying each `ABANDON:` line, once the ticket is handed back. When the tracker does not make the change, neither is posted and the closeout is refused. `ticket.returned` ends every hold on the ticket; `ticket.passed` ends none. `advance` merges a `CLOSED` ticket whose `ticket.passed` no `ticket.landed` has followed; a pass after a landing is new work that has not landed yet. Each wakes the main agent; `wait <n> worker` prints one of the two.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`ticket.released`**:
The event that follows a claim given back by `land` (reason `landed`), `suspend` (`suspended`) or `advance`'s `RELEASE` (`worker-lost`). It ends every hold on the ticket.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`ticket.regressed`**:
The event `dispatch.sh reverify` posts on a landed ticket whose criteria went red on the base branch, with that `commit` and the `failed` criteria, in the same pass that reopens it, labels it `needs-triage` and removes its assignee. It takes back the ticket's pass and its landing.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`worker.resumed`, `worker.retracted`, `worker.replaced`, `worker.lost`**:
The events about one worker session after its start, each naming it by `runner` and `session` together. `resume` posts `worker.resumed` once the runner has taken the text, or handed it over without being able to show a turn starting (exit 4). `retract` posts `worker.retracted` once the runner shows the session gone, recording whether the workspace, the slot and the claim were given back. `start <n> worker` on a ticket whose events still show a live worker stops that session through its own runner and posts `worker.replaced` naming it, then the new session's `worker.started`; the worktree, the branch and the worktree's product slot carry over to the new worker, and what the old one left uncommitted is committed on the branch first (`wip(#<n>): uncommitted work of …`). `worker.lost` is not written by the agent it is about, since a dead agent cannot write its own: the **watchdog** posts it, actor `judge`, once the ticket has been silent past its silence and the session's own runner answers `stopped`; the relay wakes the main agent on it.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`reviewer.lost`, `verifier.lost`**:
A reviewer or verifier session that stopped before its result landed, named by `runner` and `session` together, the same shape as `worker.lost` and posted the same way, by the **watchdog**, actor `judge`: the ticket was silent past its silence, the session had no `reviewer.reported` (or verdict) after its own start, and its runner answered `stopped`. Each ends that one session's hold, and not the wait of a worker run in the waiting step. The relay wakes the ticket's worker on it — the worker waiting for that result — which starts another reviewer or verifier.
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
What a child records, named for who can answer it rather than where it came from: the `kind` of its `child.opened`, and the kind `--sub-issue` takes. **`finding`**: a review finding outside the ticket, which the closing pass routes. **`contract`**: a baseline the ticket was told to follow does not hold — **the contract does not fit** — so it goes back to whoever wrote the spec or the baseline. **`deferred`**: a merely convenient change outside `## Owns`, left for a later ticket. **`decision`**: a choice only a person can make, the worker carrying on with the default; it is the child an `ABANDON: AC<n> decision` points at. **`fault`**: the pipeline itself is broken — a script, a hook, the driver, the target contract — and the agent that opens it stops. The relay wakes the main agent on a `fault` or a `decision`. In the closing pass and `NIGHT SUMMARY`, a bare *finding* means a `finding` child.
_Avoid_: `review`, `baseline`, `outside-owns`, `pipeline` (as kind names), sub-issue kind
_Home_: `mmw-v2/skills/verify-ticket/references/sub-issues.md`

**`ticket.checked`**:
One run of a ticket's criteria, or of the repository's `checks`, on one commit. Its `run` says whose: `self` for the worker's `verify-ticket.py <n>`; `reverify` for `--reverify` — the verifier's, or the main agent's on the base branch with `--actor main`, which names the main agent as the writer; `repo-checks` for the `checks` `--closeout` runs. The payload carries the full `commit`, the `result` (`met`, `unmet` or `handoff`), the counts, each criterion's outcome and evidence, the ids left unmet in `failed`, a fingerprint of the criteria it ran, on a `self` run the files under `Outside Owns:`, on a `repo-checks` run each failed command, and the product `slot` when the run held one. The comment's first line names the run and the commit and repeats gate-check's summary line, and the ledger follows, both for a person. Every reader takes the run from the event: the next run carries the newest `self` or `reverify` ledger forward, `status`'s `ac` column counts the newest, `--verdict` judges the newest `reverify` and refuses one on a commit other than `HEAD`, `--closeout` checks an `ALL MET` draft against the newest `reverify` alone — a `self` run is the party being judged reporting on itself — and `dispatch.sh reverify` counts a ticket red only on a `reverify` of `HEAD` that is not `met`. A run whose event could not be written exits 4 and counts as a run that did not happen.
_Avoid_: `self-run`, `reverify` (as the name of a comment), 自跑, 复验, `CHECKS FAILED`, `CHECKS OK`
_Home_: `mmw-v2/skills/verify-ticket/references/running-criteria.md`

**`worker.touched`**:
The event `--touched` posts on each open ticket under the same spec whose `## Owns` covers a file the worker's newest `self` run lists under `Outside Owns:`: `by` names the ticket that changed them and `files` the files, so the worker that owns them reads on its own ticket what another ticket did to them. Its comment gives each file with the `DECISIONS` sentence about it, the criterion that sentence names, and the Spec axis's judgement of it.
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
The event `--decisions` posts on the ticket once, after the review and before starting the verifier: first line `DECISIONS`, then `Decisions I made on my own` — every line so far, in the closing comment's shape — and `Outside Owns` — the `Outside Owns:` line of the newest `ticket.checked` of run `self`, with one sentence per file saying why. The Spec axis reads it and judges every line; a fix round after the verifier adds no second one, and the closing comment carries the final version. `--closeout` does not check it.
_Admitted_: `DECISIONS` comment
_Avoid_: decisions comment, 临时决策评论
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**review comment**:
The reviewer's report on the ticket, posted by `verify-ticket.py <n> --review <file>` as the `reviewer.reported` event: first line `REVIEW <base commit>..<HEAD commit>` (the refs as given, even when one does not resolve or the diff is empty), whose two commits are the event's `base` and `head` — a file that does not open that way is refused and nothing is posted — then the three axis reports under `## Standards`, `## Spec`, `## Tests`, never merged or reordered across axes, then `## In-ticket` and `## Out-of-ticket`, then one summary line per axis. The worker, which ended its turn after starting the reviewer, is woken with `#<n> reviewer.reported` once it lands, reads it off the ticket, and acks the wake.
_Avoid_: review report comment, REVIEW 评论, report (bare)
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**closing comment**:
The comment a worker leaves on handing over, written first as a **draft** file that `--closeout <draft>` checks and posts. Its fixed parts: the first line `ALL MET` or `HANDOFF REQUIRED: <abandoned> abandoned (<kinds>), <unmet> unmet, <met> met of <total>`; `Branch: … Commit: … PR: none — will be merged into <base branch> by dispatch.sh advance`; `Post-verdict:` (every commit after the one the verdict covers, with where it came from, `None` when the verdict is on HEAD); four lines per criterion, with `ABANDON:` where given; `Outside Owns:` (each file followed by the Spec axis's judgement, `reasonable` or `should not`); `skipped: [X], add when [Y]` (what was deliberately not built and the condition to build it); `Sub-issues opened:` (this ticket's sub-issues); `Counts: <met> met, <unmet> unmet, <abandoned> abandoned of <total>` (recounted at the Audit, agreeing with the first line); `Decisions I made on my own` (one line per thing the worker settled that neither ticket nor spec decides). `--closeout` posts it as `ticket.passed` when its first line is `ALL MET` and as `ticket.returned` otherwise, and that event, never the line, decides whether `advance` merges the branch. The draft is written by `verify-ticket.py <n> --draft`, so its `ALL MET` is not evidence until `--closeout` accepts it.
_Avoid_: 收尾评论, handoff comment, 收尾评论草稿, 草稿 (as a term), 本票我自己拿的主意
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`ALL MET`**:
The closing comment's first line when every criterion is met: `--closeout` refuses it when any `ABANDON:` is `failed` or `stuck`, and posts an accepted one as `ticket.passed`, the event `advance` merges on. Also the opening of one gate-check summary line shape, `ALL MET (<n> met…)`, which the first line of a `ticket.checked` comment repeats for a person; `--closeout`, `--verdict` and `status.py` read that event's `result` and counts instead.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`HANDOFF REQUIRED`**:
The closing comment's other first line, `HANDOFF REQUIRED: <abandoned> abandoned (<kinds>), <unmet> unmet, <met> met of <total>` — the way out of anything the worker cannot fix itself, held to none of the verdict's conditions. `--closeout` posts it as `ticket.returned`, swaps `ready-for-agent` for `needs-triage`, and leaves the ticket open. gate-check's summary line has a same-prefixed shape, `HANDOFF REQUIRED: <n> abandoned (met: …)`.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`Outside Owns:`**:
The files this ticket's own commits changed that no `## Owns` glob covers, along the first-parent chain since the base commit, merges excluded: listed by the worker's `self` run in its `ticket.checked` event, whose comment ends with them as an `Outside Owns:` line, and a fixed line of the closing comment, copied into the draft and explained there with the Spec axis's judgement of each file (`reasonable` or `should not`); `None` when empty. The `worker.decided` event's comment carries the same line with one sentence per file, the Spec axis judges each, and `--touched` posts a `worker.touched` event on every open ticket under the same spec whose `## Owns` covers one of the files. `--closeout` checks none of this. The question is asked of this ticket's own commits, so a run on any branch but `issue-<n>` writes `Outside Owns: not checked on <branch>, which carries more than this ticket` instead. It is an explanation, not a criterion.
_Home_: `mmw-v2/skills/verify-ticket/references/running-criteria.md`

**question gate**:
`hook.py question <host>`: the refusal of the host's question tool (`AskUserQuestion` on Claude Code, `ask_user_question` on Grok, `request_user_input` on Codex) in any session whose working directory's basename is `issue-<n>` — the ticket worktree every runner starts a worker, reviewer or verifier in, with nobody at its screen. It asks no runner. Its reason names the two ways out — take the likeliest option and record it under `Decisions I made on my own`, or `ABANDON: AC<n> decision` with `--sub-issue decision` under the ticket — so no question from a gated session reaches a screen nobody watches.
_Avoid_: form, 提问表单, BLOCKED:, MMW_AUTONOMOUS
_Home_: `mmw-v2/skills/drive-target/scripts/hook.py`

**`NIGHT SUMMARY`**:
The `spec.closed` event `dispatch.sh summary <spec>` posts on the spec when the night is over, first line `NIGHT SUMMARY <date>`, then five lines, `Closed:`, `Handed back to needs-triage:`, `Not dispatched, a blocker stayed open:`, `Sub-issues opened tonight:` (each ticket's children opened in the night window, by number and title), and `Findings routed:` (`opened/fixed/became/skipped/unread/open`, the closing pass's own account of the `finding` kind only, each child's kind and route taken from the `child.opened` and `child.closed` events on the ticket it came from, and a closed finding no `child.closed` accounts for counted `unread` — the batch's `contract`, `deferred`, `decision` and `fault` children are on the line above and not in this count). If `reverify` ran in this checkout, a `Reverify: <green>/<red>` line is appended.
_Avoid_: 夜间总结, the night summary
_Home_: `mmw-v2/skills/dispatch/references/night.md`

### Running the criteria

**ledger**:
The temporary file `AC.md` that `verify-ticket.py` writes from `## Acceptance criteria` and `## Owns` — with the ticks and evidence of the newest `self` or `reverify` `ticket.checked`, when that run ran the criteria the body states now — and hands to gate-check, the only format gate-check accepts. It cites criteria by `AC<n>` number, carries an `OWNS:` line, and is deleted after use; the ledger as the run left it goes back on the ticket in that run's `ticket.checked`.
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

**lint**:
`verify-ticket.py <n> --lint`: gate-lint, plus the ticket graph (`cycle`, dangling references, `cross-batch`), plus the worker-label check, plus the screen-contract checks. Every finding carries a problem tag and a level, `ERROR` or `WARN`; only `ERROR` affects the exit code. When the graph has no cycle and no dangling reference it prints the **start levels** — the order tickets may be started in, built from this spec's own blocking links. A batch converges when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose. It is run at the read-back step.
_Avoid_: 票图核对, the linter (for this), 启动层级
_Home_: `mmw-v2/skills/verify-ticket/references/linting.md`

**problem tag**:
The label a lint finding carries: from gate-lint `parse`, `tautological-check`, `weak-expect`, `path-read-as-regex`, `manual-gate`, `unmeasured-number`, `activity-not-outcome`, `mostly-manual`; from `verify-ticket.py` `dollar-without-m` (`ERROR`), `bad-timeout` (`ERROR`), `shared-state`, `cross-batch`, `cycle`, `duplicate-ticket`, `blocker-not-a-ticket`, `no-sub-issues`, `worker-label` (`ERROR`: no worker-grade label, or both), `screen-contract` (`ERROR`: an interface ticket naming no contract rows, a `--pages` mount that is not a page of the contract it names, an empty `boundary-check.py --run`, a `journey.py run <name>` with no directory under `.mmw/journeys/`, a `CHECK:` that stubs the application's own network, a pipeline flag the script retired, or a baseline-class source missing from `## Read first`).
_Avoid_: 问题标签
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`ERROR`, `WARN`**:
The two lint levels. gate-lint prints `ERROR` and `WARN `; `--lint`'s exit code says only whether an `ERROR` is left.
_Home_: `mmw-v2/skills/verify-ticket/references/linting.md`

### Code review

**code review**:
One round: the worker starts the reviewer with `dispatch.sh start <n> reviewer `; the dispatcher starts three general-purpose subagents, each prompted to use the `code-review` skill with a ticket, a base commit, and one axis name — Standards, Spec, or Tests — each reading `git diff <base-commit>...HEAD`; one review comment results. The round ends only with that comment: the worker ends its turn after `start`, is woken by the relay with `#<n> reviewer.reported` once the comment lands, reads the report off the ticket, and acks the wake; nothing is polled. The dispatcher holds its own turn until all three axes have answered, so that a session coming to rest means the report exists. Start exits 2: nothing was started — it is a pipeline fault: `<engine> <n> --sub-issue fault <file>`, then stop. The reviewer stopped with no `reviewer.reported` event: read its session on the runner its `reviewer.started` event names. An in-ticket finding gets one round of fixes and a run of the worker's own (`<engine> <n>`), never a re-review; an out-of-ticket finding is `--sub-issue finding`. Fixing a finding is bound by the writing rules.
_Avoid_: the review stage
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**axis**:
One of the three dimensions of a code review, each a host general-purpose subagent that re-enters the `code-review` skill through the matching axis door. **Standards axis** (`Standards reviewer`): does the change follow this repository's documented coding standards, and does the same outcome exist with less code — from the documented standards, the **smell baseline** (the twelve Fowler smells, carried in full inside the reference file and never pasted into a prompt), and `codebase-design/SKILL.md`; it asks of every hunk whether it could be less, and marks a finding `judgement call` or `hard violation`. **Spec axis** (`Spec reviewer`): does the change match what the ticket or the spec asked for, reading the baselines under `## Read first` and never the handoff package; findings are `Missing`, `Scope creep`, or `Built wrong`; it also judges every line of the ticket's `DECISIONS` comment `reasonable` or `should not`, and a `should not` is an in-ticket finding. **Tests axis** (`Tests reviewer`): are the test cases the criteria name worth trusting — its in-ticket scope is the test files and cases a `CHECK:` names, any other test file in the diff is out-of-ticket, from the **test smell baseline** copied from `tdd/tests.md` and `tdd/mocking.md`; it reports no coverage and adds no criteria the ticket lacks.
_Avoid_: 轴 (for this), Standards 轴, Spec 轴, Tests 轴, 缺项, 实现得不对, baseline smell, smell list
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**review finding**:
One item an axis subagent reports, quoting the requirement line it fails. It is **in-ticket** when it touches this ticket's acceptance criteria, a decision in the spec section the ticket names, a baseline under `## Read first`, the spec's `## Out of Scope`, the spec's `## Testing Decisions`, or a file inside this ticket's `## Owns` — then it gets one round of fixes, and `ABANDON: AC<n> failed` if the fix cannot be made; otherwise it is **out-of-ticket** and becomes a non-blocking `finding` child under the ticket (`--sub-issue finding`), labelled `needs-triage` and `mmw:child`, while the ticket still closes. The dispatcher sorts them.
_Avoid_: 票内, 票外, 票内发现, 票外发现
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**reference file**:
A document under a skill's `references/` directory, reached by a relative link from its `SKILL.md`. For code review the session's steps live in `references/session.md` and each axis has its own file; an axis subagent is told the skill and the axis name, never a path.
_Avoid_: reference (bare), 判据 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

### UI acceptance

**story**:
A product page that renders one presentational component from the same scene data the design page used, addressed as `<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`. It lives in `.mmw/stories/`; the product's `stories` command prints `origin`. No backend, no seed, no route.
_Avoid_: storybook (when this page is meant), preview page
_Home_: `mmw-v2/skills/drive-target/references/story-parity.md`

**user story**:
One line of a spec's `## User Stories`.
_Avoid_: story (for this)
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**story judge**:
`scripts/story-parity.py` beside the drive-target `SKILL.md`: it decides whether a product story matches the design page it was built from. Given `--contract` and `--pages <mount,…>` (and `--scenes` to narrow), it starts the `stories` command, opens each scene at each contract viewport, captures `[data-story-root]`, renders the design page offline with `#dc-root` pinned to that box (`frame_box`), and compares the normalised accessibility tree and pixels after sub-cell alignment. The class set is not compared. It prints `STORY OK <passed>/<total> pixel<=<worst>%` (exit 0), or one `DIFF <scene> <viewport> <pct>% (unaligned <pct>%) — <reasons>` line per failing pair (exit 1), or `NEGATIVE CONTROL FAILED` (exit 2). `--render-only` renders the design side alone. No address is on its line: a `CHECK:` names it bare, and `verify-ticket.py --tools` puts the drive-target skill's `scripts/` on the `PATH` of the shell that runs it.
_Admitted_: `story-parity.py`
_Avoid_: visual-parity.py (as the judge), interface parity, PARITY OK (the whole-product judge's success line), visual parity
_Home_: `mmw-v2/skills/drive-target/references/story-parity.md`

**scene data**:
The `data` field of a `scenes.json` entry: `{state, vals}` — that scene's `init(props)` return and `renderVals()` return, functions stripped. The handoff writes it; the product story's adapter reads the same object. A package whose `data` is missing or stale is a lint failure, not a product defect.
_Avoid_: fixture props (when this field is meant)
_Home_: `mmw-v2/skills/claude-design-blocks/references/handoff.md`

**boundary**:
In this repository the word names one class of acceptance criterion and the judge that runs it: a **boundary criterion**, in the fixed shape of `references/boundary-check.md`, run by `boundary-check.py`. It is not a word for a **seam**.
_Avoid_: boundary (as a word for a seam)
_Home_: `mmw-v2/skills/drive-target/references/boundary-check.md`

**boundary criterion**:
An acceptance criterion in the fixed shape of `references/boundary-check.md`, running `scripts/boundary-check.py --run "<the product's test command>"`: the command is run twice in this process's cwd, first as written (must exit 0), then with `MMW_NEGATIVE=1` (must exit non-zero). Prints `BOUNDARY OK <n>/<n>`, or `MISS <command>` when the first pass is already red, or `GREEN WITHOUT INTERACTION <command>` when the second pass is also green. Mocking the product's own API client module is the allowed seam; stubbing `fetch`, msw, nock or fetch-mock is not.
_Admitted_: boundary check
_Avoid_: wiring criterion, wiring-check.py, WIRING OK
_Home_: `mmw-v2/skills/drive-target/references/boundary-check.md`

**mutation check**:
The second pass of a boundary criterion: the same command, with `MMW_NEGATIVE=1`, must go red. The product's shared interaction helper does nothing under that variable, so an assertion that does not depend on the click stays green and is refused. It is mechanical; a reviewer does not read the test to decide whether it can fail.
_Home_: `mmw-v2/skills/drive-target/references/boundary-check.md`

**journey**:
One Playwright script under `.mmw/journeys/<name>/`, run against the real product on this machine. `scripts/journey.py run <name>` claims the lease, runs `start`, runs `discover`, puts the addresses and lease variables into the environment, runs the script, and runs `stop` whether the script succeeded or not; then runs the script once more as its **negative control**. Prints `JOURNEY OK <name>`, `JOURNEY FAILED <name> at <last line>`, or `JOURNEY GREEN WITHOUT PRODUCT <name> at <last line>`. Quantity and content are the owner's; the default three are money, the login gate, and one submit chain.
_Admitted_: `journey.py`
_Avoid_: wiring check (when a whole-product run is meant), parity run
_Home_: `mmw-v2/skills/drive-target/references/journey.md`

**`.mmw/harness`**:
The directory in a consuming repository that holds start-the-stack, vendor stubs, account seeds, the few seeds a journey uses, and the entry that records an action that would leave the machine. Product answers live in `.mmw/` (`target.json`, `harness/`, `journeys/`, `stories/`); `harness-guard.py` fails a name that leaks outside `.mmw/`, `tests/`, `scripts/dev/`, or a file `leaves_machine` names.
_Avoid_: reach script, `scripts/testing/` (when this directory is meant)
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

**negative control**:
The pair each judge builds to prove it can fail. The story judge's is judged before any real result: after the first scene at the first viewport, the baseline server serves that scene's own address with an error banner in the served bytes, the story page is captured again, and the two must differ — equal means the product capture read the design's server, and the run stops with `NEGATIVE CONTROL FAILED`. The boundary criterion's is the **mutation check**. The journey's runs last, after `stop`: the script runs again with every discovered address repointed to a closed port and `MMW_JOURNEY_NEGATIVE=1` set, and a second pass is `JOURNEY GREEN WITHOUT PRODUCT`.
_Avoid_: 负控制, GREEN WITHOUT TRANSPORT
_Home_: `mmw-v2/skills/drive-target/scripts/story-parity.py`, `mmw-v2/skills/drive-target/scripts/boundary-check.py`, `mmw-v2/skills/drive-target/scripts/journey.py`

**normalisation**:
How an accessibility tree is read before comparison: as the sequence of its named nodes in reading order — role, name or text, and state attributes — each followed by ` < ` and its nearest named ancestor, with unnamed wrappers and landmark names dropped. One normaliser, in `screen_driver.py`, serves the story judge and the target trees. The accessibility tree walks the whole subtree under `[data-story-root]` or `#dc-root`; the pixel judge sees only that box intersected with the viewport, on both sides.
_Avoid_: 归一化, ARIA 归一化, ARIA 树, 视口
_Home_: `mmw-v2/skills/drive-target/references/story-parity.md`

### Screen contract

**screen contract**:
`docs/specs/<effort>/screen-contract.yaml`. The **control axis**, `rows`: one row per user-visible behaviour — the control (`trigger`, by role and accessible name), its `precondition`, the `scenes` it is visible in, what it `calls`, which field feeds each value it `shows`, what state is `next`, what `on_failure` shows, where the behaviour was decided (`source`), and whether design and backend agree (`gap`). `pages` names each design page's story id (`mount`) and the component that owns it; only an `App · ` page may carry `route`. `scenes` names which design page each scene of `scenes.json` belongs to. It also carries `target.kind`, `viewports`, `retired_ids`, `volatile_values`, `readme_dispositions`, `backend_without_ui` and `proposed_operations`. It carries no address, no `observe`, no locating pin. Written by `align-screens` on the alignment ticket; read by `to-spec`, `to-tickets`, `implement`, the Spec axis, the story judge, the boundary check and `verify-ticket --lint`. It is the behaviour baseline of an interface, beside the handoff package as its look-and-copy baseline; the two never bind the same thing.
_Avoid_: UI contract, interaction table, 界面合同表, 对齐表
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

**alignment ticket**:
The last ticket of a wayfinder map whose destination has an interface: a `grilling` ticket, blocked by every decision ticket and by the ticket that produces the handoff package, resolved by running `align-screens` and closed when every row's `gap` is `aligned`.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**gap list**:
The rows of a screen contract whose `gap` is `design-only` or `backend-only`, written by `align-screens` for the person to settle — the one judgement in that skill that is theirs.
_Avoid_: 差集
_Home_: `mmw-v2/skills/align-screens/SKILL.md`

**contract ticket**:
The first ticket cut from a spec with a screen contract: `.mmw/` in full (target.json, harness, journeys, stories and adapters), the interaction helper the boundary check uses, a `journey.py run smoke` criterion that starts the stack and logs in, and the harness guard. Every other ticket of the batch is blocked by it. Interface tickets own by design page: one story criterion (`--pages`) and one boundary criterion per `calls` row.
_Avoid_: 合同票, prefactor ticket (for this one), addressing self-check
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`screen_driver.py`**:
`scripts/screen_driver.py` beside the drive-target `SKILL.md`: the shared runtime `story-parity.py` and `extract_skeleton.py` import — the contract's pages and scenes, `.mmw/target.json` and the declaration of its fields (`FIELDS`), the baseline server and its CDN answering (`vendor/`, cache, network), `capture`, and the normaliser. Nothing in it judges. Run as a command, `screen_driver.py target --check` is the setup-time bar for one repository. The contract lint loads this file in-process: kinds from `KINDS`, the `.mmw/target.json` check through the function `target --validate` runs.
_Avoid_: the driver module, 共用驱动, Adapter (the driver class)
_Home_: `mmw-v2/skills/drive-target/scripts/screen_driver.py`

**target**:
What kind of product this repository is, named in the contract as `target.kind` — `electron`, `web-spa`, `web-server-rendered`, `chrome-extension`. The repository answers for this product on this machine in `.mmw/target.json`, in the fields `screen_driver.py`'s `FIELDS` declares, which `screen_driver.py target --check` prints with one sentence and one example each, exiting 0 once the file is complete. The list does not change with the kind. The contract carries no `adapter` key.
_Avoid_: platform (bare), 目标 (as a term), 适配器 (and `adapter`, as a word for anything on the target side; the file name `.release-adapter.json` and the key template's `--adapter` flag are literals a program reads and stay), target.adapter, the nine questions
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

**`.mmw/target.json`**:
The consuming repository's machine facts, read by the runtime and never written in a contract or a criterion: what brings this product up on this machine, what takes it down, where it answers, where its story pages and journeys are, and what it does that reaches past the machine. Which fields those are is `screen_driver.py`'s `FIELDS`, printed one sentence and one example each by `screen_driver.py target --check`. Addresses change per machine and per worktree; this file is where they are answered afresh.
_Avoid_: target config, 地址文件, reach (the target.json field), transport_off, transport_on
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

**`checks`**:
The optional key of `.mmw/target.json`: a list run in order at the repository root by `--closeout` only, after the draft is accepted and before an `ALL MET` ticket closes. An entry is a command string, held to `DEFAULT_TIMEOUT`, or `{"run": …, "timeout": …}` held to its own bound. The run is posted as a `ticket.checked` of run `repo-checks` before the closing comment: `met` when every command exited 0, and the ticket closes; `unmet` with each failed command and its last 20 lines when any did not, and the ticket stays open, still assigned and in the agent queue. A `checks` value that is not a list, an entry of another shape, or a file that is not JSON, is an `unmet` run naming that problem, not absence. `--reverify`, `--lint`, `--check-only`, and a `HANDOFF REQUIRED` draft do not run them. A repository without the key is unchanged.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**lease**:
One run's share of this machine: a registration of `worktree path -> slot` in `~/.mmw/leases`, recording the repository's git directory. A worktree claims it at the first run of its criteria that needs the product — writing code takes none, and neither `start` nor `adopt` takes one — and keeps it until its ticket's work ends, at an event in `SLOT_ENDS`, since the worker's run, the verifier's reverify and the closeout's checks all want the same application; a replaced or lost worker's worktree keeps it for the worker that carries on there. `advance` and `land` give it back when they archive the workspace, `advance` also when it gives back a lost worker's claim, `--closeout` when it hands the ticket back, `suspend` and `retract` with the claim; the main agent's `reverify --actor main` in the main checkout gives its slot back as each run ends. `lease.py claim | env | run | release | list | count` is the whole surface. Two limits bound a claim: the machine's `MMW_LEASE_SLOTS`, and the product's `instance.max`, which counts every claim made from the repository wherever its directory is. A claim past either is not taken — `claim` exits 4 naming the limit and who holds the slots — and the run waits under a `worker.queued` event. The count and the take happen under one lock on the registry, the take is atomic (`O_CREAT | O_EXCL`), there is no fallback to a second slot, and **nothing in it ever ends a process**: `release` refuses while anything still listens on the slot and names the pid and the directory. The driver claims the lease before it runs any command `.mmw/target.json` declares.
_Admitted_: instance lease
_Avoid_: 租约 (as a term), seat, reservation
_Home_: `mmw-v2/skills/drive-target/scripts/lease.py`

**slot**:
What a lease hands out: a block of ports and a data directory that no other slot overlaps, numbered from 0. `MMW_LEASE_SLOTS` (8) is how many this machine holds, `MMW_LEASE_PORT_BASE` (21000) and `MMW_LEASE_PORT_STRIDE` (20) where the blocks start and how wide they are. Bare `slot` is always this one.
_Avoid_: 槽位, port range (for this), seat
_Home_: `mmw-v2/skills/drive-target/scripts/lease.py`

**instance**:
One run of a product on this machine, and the optional `instance` field of `.mmw/target.json`: how many of them one machine holds at once, and how a run takes one. `.mmw/target.json`'s `"instance": {"max": <n>, "why": "<what stops a second one>"}` is where a repository whose product cannot move says so: every claim the repository holds counts toward `max`, the main checkout's included, and a run past it waits for a slot under a `worker.queued` event; `advance` still starts every frontier ticket. `discover` prints `instance`, a readable name for messages, and `instance_check`, one `observe` line whose truth means the product answering is the one this run started — which is what makes question 2 mean *answering and mine*.
_Avoid_: 实例 (as a term)
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

**`MMW_INSTANCE`, `MMW_SLOT`, `MMW_PORT_BASE`, `MMW_PORT_COUNT`, `MMW_DATA_DIR`, `MMW_AUTOMATION`**:
The six variables a lease puts into the environment of every command `.mmw/target.json` declares: a readable machine-unique name for this run, the slot number, the first port of its block, how many ports the block holds, a directory it owns, and `1` as the signal that what would leave this machine is to be neutralised and recorded instead. A repository reads them **at the moment it starts a process, never into the session or the test environment**: a suite that asserts its product's registered port number is right to, and a derived port leaking into it turns a correct suite red.
_Home_: `mmw-v2/skills/drive-target/scripts/lease.py`

**`stop`**:
The key of `.mmw/target.json` that ends what `start` started and nothing else — the only way a run may end a process, since `hook.py pretool` refuses `kill`, `pkill`, `killall` and `xargs kill` and sends the reader to it. It ends only what this run recorded as its own, leaves a neighbour's product alone, and exits 0 with nothing of its own to end. It does not release the lease; the driver does. A repository that declares `start` declares `stop`, or the refusal points at a command that does not exist.
_Avoid_: 停止命令, teardown
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

**`leaves_machine`**:
The required key of `.mmw/target.json` that answers what this product does in a run that reaches past the machine — opening the system browser, calling a paid service, writing a machine-global location — and how the run neutralises and records each under `MMW_AUTOMATION=1`. `[]` is an answer; a missing key is not, because a run that reached a live service looks exactly like one that did not.
_Avoid_: 离机操作, side effects (for this)
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

**mount**:
A design page's `mount` in the contract's `pages`: the story page id the product serves as `?page=<mount>`. Declared by the person writing the contract, never derived from rows; unique across pages. A story criterion names the ticket's mounts with `--pages`. `--mount` is a retired flag of `story-parity.py`, listed under `retired` in `verify-ticket.py`'s `PIPELINE_SCRIPTS` and reported by `--lint` as `[screen-contract]`; the live name is `--pages <mount,…>`. It is also the value of `data-screen` on the one product element this page *is*, when the surface carries that attribute.
_Avoid_: mount point (for this), 挂载点, data-screen-label, test hook (for this)
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

**target trees**:
`docs/specs/<effort>/targets/<page>.aria` and `<page>.classes`, one pair per design page, written by `extract_skeleton.py --targets` with the story judge's normaliser: every scene's normalised tree and the class names in that subtree, headed by the sha256 of `scenes.json` and of the page. The handoff package's behavioural counterpart and a derived view of it — the package is the baseline, the tree the view, the hashes what keeps them from disagreeing (the contract lint fails when they do). An interface ticket lists its pages' pair under `## Read first`.
_Avoid_: 目标树, target elements, expected tree
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

**`volatile_values`**:
A top-level list on the screen contract of display values the seed must not write — a wallet balance belonging to an external account, not a difference to hide. Each entry is a `page`, a `trigger` (role and accessible name, the same shape as `retired_ids`), one line of `reason`, and the previous named node when another node on the scene shares its role and its name with the digits removed. The story judge masks that node on both sides before comparing; how the mask is applied and matched is in the contract format.
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

### Dispatch and the night

**landing pipeline**:
The whole path from spec to closed ticket, made of stations that each have an entry here: by night **dispatch**, **preflight**, the worker's closing steps, **closeout**, **land**, **advance** and the **收口轮**; in the morning **reverify**, **NIGHT SUMMARY** and the triage queue. What feeds the night — **publish**, a spec, its tickets, their lint — is the day's work and has its own entries. Every rule of the path lives with its station; this entry only names them.
_Admitted_: ticket pipeline (in triage text)
_Avoid_: 流水线, this pipeline (as a name), 落地流水线
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**publish**:
Creating the spec or the tickets as GitHub issues (`publish to the issue tracker`): each ticket as a native sub-issue of its spec, labelled `ready-for-agent` plus a worker grade, or `ready-for-human`. The **read-back** step follows: every ticket is read back — title and `## What to build` describe one slice, the native edge count matches, the spec's sub-issue count equals the batch, `## Read first` and `## Seam` are non-empty — and every ticket with criteria is run through `--lint`.
_Avoid_: 发布 (as a term), 出票 (as a term), 回读 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**dispatch**:
Turning a ticket into a running session in its worktree: `dispatch.sh start <n> worker|reviewer|verifier`. The script checks the ticket may start, reads the role's live-table row, opens the workspace and records the base commit, has tonight's runner start the session, writes its started event (`worker.started`, `reviewer.started` or `verifier.started`) on the ticket, and prints the session id. The caller gives the ticket number and the kind; the worker-grade label picks which worker row. A ticket or session that has been through it is **dispatched**.
_Avoid_: 派发 (as a term), run (as a dispatch.sh verb)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`dispatch.sh`**:
The dispatch skill's script: `check <spec>`, `open <spec>`, `open-ticket <n>`, `adopt <n>`, `self`, `advance <spec>`, `land <n>`, `start <n> worker|reviewer|verifier`, `retract <n>`, `wait <n> worker|reviewer|verifier`, `ack <n> <event>` / `ack relay.recovered`, `resume <n> "<text>"`, `status <spec>`, `reverify <spec>`, `route <ticket> <child> fixed|stale|became-ticket [<new ticket>]`, `summary <spec>`, `suspend <spec>`. It starts, messages, asks after and stops a session only through the adapter of the runner that runs it; it records `branch.issue-<n>.mmw-base`; reads the worker-grade label and nothing else to pick the worker row. The skill's own text calls it `<dispatch>`.
_Home_: `mmw-v2/skills/dispatch/SKILL.md`

**dispatch line**:
The sentences a session is given when started — which skill to use, on which ticket, and that nobody is watching. A worker gets `Use the implement skill to work ticket #<n>.` plus the autonomous sentence; a reviewer gets `Use the code-review skill to review ticket #<n> from base commit <base-commit>.` plus the same sentence; a verifier gets `verify #<n> 按 <path> 行事` with no autonomous sentence. The autonomous sentence is `You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work.` A live worker gets `resume` instead.
_Avoid_: 派发 (as a term)词, prompt (bare)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**check**:
`dispatch.sh check <spec>`: runs `install.sh --check`, confirms tonight's runner has an adapter, resolves the live-table row of each worker grade, the reviewer and the verifier against that runner's catalog, confirms the host of each is `available` in `paseo provider ls --json` when Paseo is tonight's runner, and confirms every queued ticket has at most one worker-grade label that the live table has a row for. Exit 0 all passed; exit 2 one or more failed, stderr one `dispatch: …` line per failure. Do not `open` on 2.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**open**:
`dispatch.sh open <spec>`: the night begins. The relay opens a **watch** on the spec with the calling session as its main agent, named by the runner and session its adapter's `self` reads (`relay.py start --spec <spec> --runner <runner> --session <session>`), starting the relay when none runs, and `spec.opened` is written on the spec naming that runner and session. Opening the same night again makes the calling session its main agent and touches no other watch; a spec one of whose tickets is already watched on its own is refused before anything is written. A `spec.opened` that could not be written closes the watch this call opened. `advance` refuses a night that is not open, and `summary` and `suspend` close its watch. Exit 0 opened; exit 2 nothing opened, the reason on stderr.
_Avoid_: register (as the name of this), 开夜 (as a term)
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**open-ticket**:
`dispatch.sh open-ticket <n>`: what `open` is for one ticket outside a night. The relay opens a watch on ticket `<n>` alone with the calling session as its main agent; nothing is written on the ticket. A ticket a night's watch already covers is refused. `land <n>` closes that watch once nothing works the ticket any more. Exit 0 opened; exit 2 nothing opened.
_Home_: `mmw-v2/skills/dispatch/references/one-ticket.md`

**start**:
`dispatch.sh start <n> worker|reviewer|verifier`: one ticket, one agent. Tonight's runner — `MMW_RUNNER`, the live table's `runner` row, the runner the caller runs in when an adapter exists for it, then `orca` — starts the session through its adapter, with the agent's live-table row resolved against that runner's catalog; `start` writes the session's started event on the ticket and prints the session id. A start the runner refuses is refused once: no retry, no other host. On a ticket whose events still show a live worker, `start <n> worker` replaces it: that session is stopped through its own runner, `worker.replaced` names it, and the new worker starts in the same workspace; a worker that will not stop is refused and nothing starts beside it. A worker started in a standing workspace an earlier worker of the ticket left with uncommitted edits first commits them on the ticket branch, and a start whose edits cannot be committed is refused. A start takes no product slot. A session whose started event the tracker will not take is stopped again and the start refused, since no command could find it. The worker row of the live table is chosen by the ticket's `junior-worker` / `senior-worker` label; the reviewer's base commit is read from `git config branch.issue-<n>.mmw-base` by the script; the verifier's first prompt names the `verdict` skill and the ticket. A ticket no running relay watches is refused too: its result would wake nobody. It cuts the worktree under the main checkout whichever worktree it is run from, so a worker starts its reviewer and verifier from its own worktree. Exit 0 started; exit 2 refused (`REFUSE`, reason on stderr), nothing started.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**adopt**:
`dispatch.sh adopt <n>`: the calling session becomes ticket `<n>`'s worker, for a session that picked the ticket up itself and was started by no `start`. Run from the ticket's worktree on `issue-<n>`, before claiming, it writes `worker.started` with the session's own runner and session (its adapter's `self`) and the facts `start` writes — the grade's live-table row, the worktree, branch and base — plus `adopted: true`, takes no product slot, and makes sure a relay watches the ticket: the watch already covering it, or a watch of the ticket alone with this session as its main agent. A session that adopted a ticket outside a night is its own main agent, so it hands `land <n>` to the user rather than running it from the ticket's worktree. The same session adopting again writes nothing; a ticket another live worker holds is refused. Without it no event names the session, so its reviewer's report would wake nobody and `start <n> reviewer` would refuse. Exit 0 adopted, the session id on stdout; exit 2 refused.
_Avoid_: claim (for this; claiming is `--preflight`)
_Home_: `mmw-v2/skills/dispatch/references/inside-a-ticket.md`

**self**:
The fifth verb of a runner's adapter, and `dispatch.sh self`: the runner and session the calling process itself runs in, as `runner<TAB>session`. Each adapter reads its own runner's mark on the process — Paseo's `PASEO_AGENT_ID`, Orca's `ORCA_TERMINAL_HANDLE`, the name `herdr agent list` gives the agent in Herdr's `HERDR_PANE_ID` — and answers 0 with the id, 3 when the process runs in none of its sessions, 1 when it does and the id cannot be read (a Herdr agent with no name, an Orca terminal with no handle). `dispatch.sh self` asks the innermost runner first — Paseo, then Herdr, then Orca — since a wake sent to an outer terminal is typed into whatever it shows, and it needs no live table. `open`, `open-ticket`, `adopt` and `ack` name the calling session with it, and `verify-ticket.py` names the session a `ticket.refused` is written by.
_Home_: `mmw-v2/skills/dispatch/scripts/runners/`

**retract**:
`dispatch.sh retract <n>`: take back what `start` left once the ticket's session is gone — commit what its worker left uncommitted on the ticket branch, archive the workspace, give back the product slot if its worktree holds one, give the claim back if this pipeline holds it, then write `worker.retracted`, which ends that session's hold so `advance` can start the ticket again. A session its runner still shows alive, or cannot answer for, is refused: that is a running worker, not a failed start; so is a ticket whose events cannot be read. It does not merge. The branch stays, so the next `start` reuses it.
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
`dispatch.sh reverify <spec>`: on the current branch, every ticket under the spec whose events show it passed and landed (`status.py --reverify-plan`) is run through `verify-ticket.py <n> --reverify --actor main`, whose `ticket.checked` names the main agent as its writer; a run that needs the product claims a slot that counts toward `instance.max` like any worktree's and gives it back as the run ends. One that passed and has not landed is named on stderr and not run. Exit 0 all green; exit 1 at least one red — a `reverify` `ticket.checked` of `HEAD` that is not `met` — that ticket is reopened, labelled `needs-triage`, its assignee removed, and a `ticket.regressed` event names the failing `AC<n>` that event gives; exit 2 a ticket could not be re-run at all — it could not start, its run was not recorded, or it waited for a slot and none came free — so nothing was judged on it and the rest of the batch is skipped. A run that could not start is never a red ticket.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**summary**:
`dispatch.sh summary <spec>`: posts the `spec.closed` event on the spec, first line `NIGHT SUMMARY <date>`. If `reverify` ran in this checkout, a `Reverify: <green>/<red>` line is appended. Exit 0 posted; exit 2 it could not be posted.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**status.py**:
`scripts/status.py` of the dispatch skill, six read-only forms: `--table <spec>` (the `status` table), `--advance-plan <spec>` (what `advance` has to do, in order), `--reverify-plan <spec>` (the landed tickets `reverify` runs), `--land-plan <n>…` (what `land` has to do), `--worker-grades <spec>` (the worker-grade labels of every ticket in the queue), `--summary <spec>` (prints the night summary; does not post it). Its one source is the tracker: the spec's tree of tickets and their children, read in one query by `tree.py`, and each ticket's state, labels, assignees, blocking links and comments. Where a ticket stands — which sessions were started on it and on which runner, whether it is held, passed, landed or returned — is the fold, through `events.py`; no runner is asked. It keeps no state file. The criteria count comes off the newest `ticket.checked` of the criteria.
_Avoid_: board.py, board
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**phase**:
The `phase` column of `status`: the name of the ticket's newest event, `closed` on a `CLOSED` ticket that carries none, or `-`. It is shown and never decided on; what a script decides from is the fold.
_Avoid_: stage (for this), selfcheck, implement (as a phase), closeout-rejected, handoff (as a phase)
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**preflight**:
`verify-ticket.py <n> --preflight`, the worker's first step: six checks — on the ticket branch, no uncommitted tracked changes, ticket state `OPEN`, labelled `ready-for-agent`, no open blocker, no assignee — then the claim and its `ticket.claimed` event, printing `READY: #<n> claimed on issue-<n>`. Any failure posts `ticket.refused`, prints its first line `NOT_READY: <reason>` and exits 2. The checks are all in the script; the model does not perform them one by one.
_Admitted_: start-of-work guard
_Avoid_: 开工守卫, 开工核对, the guard (for this)
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**claim**:
Setting the ticket's assignee to oneself, `gh issue edit <n> --add-assignee @me`: the first write action after preflight's checks pass, and the session's first write, followed by a `ticket.claimed` event that begins the ticket's hold. A claim exists only on the tracker, and the frontier takes unassigned tickets only, which is what keeps a second worker off a ticket somebody is already working. Six paths take a claim off: the closeout, the hand back to triage, `land`, `advance`'s **give a claim back** (the `RELEASE` line) for a claim whose worker is gone, `suspend`, which gives back every claim of the batch, and `retract`, which gives the claim back once a ticket's session is gone. A session that ends any other way — a crash, a machine restart, a workspace archived from outside this pipeline — would otherwise leave the ticket off every frontier for good, with an empty frontier as the only sign of it.
_Admitted_: give a claim back (for the third path)
_Avoid_: 认领 (as a term), assign to oneself, release (in prose, for taking a claim off; the printed literals `RELEASE <n>`, the `released` of an `advance` or `land` summary line, and `released the claim on #<n>` stay as they are)
_Home_: `docs/agents/issue-tracker.md`

**`RELEASE`**:
The line `status.py --advance-plan` prints for a ticket whose claim is to be given back, between the `MERGE` lines and the `DISPATCH` lines, and which `dispatch.sh advance` carries out as `gh issue edit <n> --remove-assignee @me`. Four conditions together: the ticket is open, it is in the agent queue, this pipeline's own account is on it, and an event on it has ended every hold on it — so its worker is gone, whichever runner and machine it ran on. A claim no event ever showed held is kept, and so is the claim on a ticket with an unreadable event; each prints why on stderr. `advance` follows the write with a `ticket.released` event, reason `worker-lost`. A standing workspace is not a run: a worker holds its ticket only while its events show it live. A ticket usually carries a `RELEASE` and a `DISPATCH` of the same plan, since the claim is what kept it off the frontier and the frontier is read after the releases above it; `start` then reuses the standing workspace. Each one prints a line of its own. It is not `lease.py release`, and not `.mmw/target.json`'s `release` capability.
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**advance**:
`dispatch.sh advance <spec>`: first merge the branches of the tickets that closed, by closing time from earliest to latest, into the base branch — a ticket is merged when it is `CLOSED`, its events carry a `ticket.passed` no `ticket.landed` has followed, its branch exists, and it is not already an ancestor; one merge commit each, and `ticket.landed` written on the ticket once its branch is in `HEAD` (a branch already there is recorded as landed without a merge); `MERGE_TRIES` retries against a worker's commit in its own worktree holding the shared `.git` lock, and exit 2 when every try fails — then **land** each merged ticket (archive its workspace, giving back its product slot first when it holds one), give back the claims whose workers are gone, and dispatch the frontier, all as `status.py --advance-plan` lists it (`MERGE <n>`, `RELEASE <n>` and `DISPATCH <n>` lines, in that order — the **advance plan**). It starts each dispatched ticket's session through `start` and prints one session id per ticket. A conflict is left in place with exit 3 and a **conflict report** on stderr; the main agent resolves it with `resolving-merge-conflicts` — never `--abort` — runs this repository's checks, commits the merge, and runs `advance` again. Uncommitted changes in the working tree give exit 2. It ends with the **advance summary line** `advance #<spec>: merged <m>, already in <s>, released <g>, started <k>, refused <r>` and may be run repeatedly; a run in which the runner refused any start exits 4, since that ticket stays on the frontier and nothing wakes anyone about it. It starts every frontier ticket: `instance.max` holds no start back, and bites at a worker's first run that needs the product (see **lease**).
_Avoid_: 并回来 (as a term)
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**land**:
`dispatch.sh land <n>`: merge the ticket branch into the branch the caller is on and write `ticket.landed`, archive its workspace, stopping every session the ticket's started events name, give back its product slot if its worktree holds one, and give its claim back with a `ticket.released` event (reason `landed`). It takes a ticket number and never a spec, which is the whole reason it exists: a ticket dispatched outside a night belongs to no batch, so `advance` can never reach it, and before this there was no command that ended one. Archiving a workspace deletes the worktree directory and takes the worker, reviewer and verifier inside it, leaving the branch; that is why the merge goes first, and why a ticket that closed without a `ticket.passed` and whose branch is not in `HEAD` is named on stderr and left standing rather than archived (exit 1). `advance` does the same four things for a whole batch after its merges. What a ticket needs before any of it is that the tracker says it is over: `CLOSED`, or open and handed back to triage. Open with no verdict either way is untouched.
_Avoid_: 落地 (as a term), 收尾 (that is the worker's closing steps), archive the ticket, finish (as a name)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**suspend**:
`dispatch.sh suspend <spec>`, the decision to give a night up before it is over, taken when the fault is in the pipeline rather than in a ticket. It stops every session still holding a ticket of the batch — its worker, and a reviewer or verifier whose result is not in — through that session's runner's `stop`, which interrupts it mid-turn, unless the runner already shows it stopped, and leaves the workspace and the branch standing; it posts `spec.suspended` on the spec and on every ticket still in the agent queue, gives back every claim with a `ticket.released` event (reason `suspended`), and gives back every lease slot the batch holds. That is what lets `advance` take the same batch up again once the fault is fixed: each ticket is unclaimed, no agent holds it, and its standing workspace is reused. A ticket one of whose sessions could not be stopped, or whose events cannot be read, is left exactly as it was and named on stderr. `lease.py` refuses a slot something still listens on, and `suspend` reports that on stderr and exits 1 rather than forcing it. Exit 0 when nothing was left over, 1 when something was, 2 when nothing was touched. `ABANDON:` on a criterion is unrelated: it says one criterion was given up, and this says a night was.
_Avoid_: abandon (as the name of this), 收夜, give the night up (as a name)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**night**:
Everything between the last ticket published and the morning: the user says it starts, the main agent runs `check`, then `open`, then `advance`, and ends its turn; on each **wake** it reads `status`, decides — `resume`, `retract`, or reading a stopped session on the runner its `worker.started` event names — runs `advance` once, and acks the wake. A ticket leaves the night by its worker's closing comment, or by staying in the agent queue behind an open blocker all night, which the `Not dispatched, a blocker stayed open:` line of `NIGHT SUMMARY` lists. The night ends when the frontier is empty and `status` shows no live agent: then the **收口轮** if open `finding` children remain, then `reverify`, then `summary`, which closes the night's watch.
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

**morning**:
The user takes over with the two **morning queries**, `is:open label:needs-triage` (which `triage` reads) and `is:open label:ready-for-human` (which the user reads); the commands are in `docs/agents/issue-tracker.md`.
_Avoid_: 早上 (as a term), 早上两条查询, the two morning queries
_Home_: `docs/agents/issue-tracker.md`

**continue**:
The word the main agent appends when it `resume`s a live worker: `resume <n> "<what you settled, then: continue>"`. The session is alive and holds everything it read and wrote, so it resumes at the closing step `implement`'s resume table gives for what the ticket carries: `ticket.checked` events and the `reviewer.reported`, `worker.decided`, `verifier.passed` and `verifier.failed` events.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**hand back**:
Swapping `ready-for-agent` for `needs-triage` and leaving the ticket open: `--closeout` does it on `HANDOFF REQUIRED` (printing `HANDED BACK: #<n> is now needs-triage and stays open`). `reverify` does a related move on a landed ticket that went red: reopen, add `needs-triage`, remove the assignee, write `ticket.regressed`. `triage` reads such a ticket from its comment trail instead of reproducing it.
_Avoid_: 交回, handed back (as a name)
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**triage**:
The skill that moves an issue from outside through the state machine of triage roles: it reads the `needs-triage` queue, recommends one of the four outcomes (`needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix` — staying at `needs-triage` is not one), posts an agent brief at the evaluation stage, and ends every comment with the disclaimer. An issue judged to be agent work enters the landing pipeline through `to-spec` and then `to-tickets`; tickets `to-tickets` wrote are not triaged.
_Avoid_: 人拍板
_Home_: `mmw-v2/upstream/skills/engineering/triage/SKILL.md`

**relay**:
`scripts/relay.py` of the dispatch skill: it turns events on the tracker into wake-ups for the session waiting on them. Every `--interval` seconds (default 30) it reads the comments of every ticket its **watches** cover — tickets outside a night, or the sub-issues of a night's spec, listed again every cycle — and for each event its `WAKES` table names writes one row into the wake queue and hands that row to the runner of the session it names. It reads a ticket in full when it starts, since a relay that was down cannot assume it missed nothing. It decides nothing — whether to advance, resume, retract or stop stays the main agent's — and writes nothing to the tracker: its only writes are files in the state directory. A stretch with no good poll longer than `--grace` (default three intervals) is announced once to every watch's main agent, as a `relay.recovered` row ahead of the events it recovered. When an event that gives a product slot back lands on any watched ticket, every watched ticket still waiting under an older `worker.queued` gets one `worker.queued` row for its worker. One relay runs per repository, holding `relay.lock`, and carries every watch in `watches.json`. `relay.py start` opens a watch — refusing, with nothing written, a session its runner shows stopped or a watch that shares a ticket with an open one — and runs the relay detached when none runs; `stop` closes one watch and ends the process with the last (forgetting the last good poll, so the next start announces no stretch for a closed night); `watching` says whether it sees a ticket. Every ten cycles it asks each watch's main agent's runner `liveness`, and closes the watch of one answered `stopped` at every ask for an hour. `dispatch.sh open`, `open-ticket` and `adopt` open watches; `summary`, `suspend` and `land` close them.
_Avoid_: board.py, board, watcher (as a name)
_Home_: `mmw-v2/skills/dispatch/scripts/relay.py`

**watch**:
What the relay reads and whom it wakes about it: a night's spec, whose sub-issues are listed again every cycle, or tickets outside a night. `open`, `open-ticket` and `adopt` open one with the calling session as its **main agent**, and `watches.json` in the state directory keeps it under `spec:<n>` or `tickets:<n>[,<n>...]`. Two watches never share a ticket, so a ticket's main-agent wakes have one recipient. It is closed by `summary`, `suspend` or `land`, or by the relay itself when its main agent's runner has answered `stopped` at every ask for an hour.
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
`$MMW_HOME/state/<owner>__<name>/` — `MMW_HOME` defaults to `~/.mmw`, the root `lease.py` keeps its registry under — one per repository, owner and name lowercased, created with mode 0700. It holds every file a long-running MMW process keeps about that repository on this machine, and nothing about it is kept anywhere else. The relay's files there are `queue.jsonl`, `queue.seq`, `queue.lock`, `seen.json`, `watches.json` (every open watch and its main agent; it outlives the process), `beat.json`, `gap.json`, `relay.lock`, `relay.json` (the running relay's pid and identity) and `relay.log` (what started relays printed); the watchdog's are `watchdog.lock`, `watchdog.json` (its **heartbeat**) and `watchdog.log`, and the turn guard's is `guard.log`. A file in it is replaced in one step, so a reader sees the old one or the new one, and a file that is there but is not JSON is refused rather than read as absent.
_Avoid_: state file (for a ticket's state; that is the fold)
_Home_: `mmw-v2/skills/dispatch/scripts/statedir.py`

**lock record**:
What a lock file in the state directory holds while its lock is taken: one JSON object with the holder's `pid`, its process `identity`, `since` and `purpose`. The kernel's `flock` on the file is what excludes; the record only says who is in there, for a reader that will not take the lock — a shell script, a watchdog, a refusal that has to name the holder. A pid alone does not name a process, because the system hands a dead process's pid to the next one, so the record names a live holder only when its pid runs now **and** that process's identity — its start time as `ps -o lstart=` prints it, in UTC and the C locale — is the recorded one. A record that fails either is stale and names nobody; the kernel let go of the lock when its holder died, and the next holder overwrites it. A holder that exits normally empties it.
_Admitted_: process identity (for the start time)
_Home_: `mmw-v2/skills/dispatch/scripts/statedir.py`

**watchdog**:
`scripts/watchdog.py` of the dispatch skill: the second and third layers of liveness, one process per repository while a watch is open, not an agent and spending no tokens. It holds `watchdog.lock` for as long as it runs and writes its **heartbeat** every round (default every 60 seconds). Each round it checks the **relay** — its lock record names a live process, its last good poll is within its grace — and folds every ticket the relay's watches cover, less the closed sub-issues of a night's spec: a closed ticket's worker has handed in its work. For a ticket that is held and has had no event for `--silence` seconds (default 600), and every round for a ticket in the waiting step (the fold's `waiting`: quiet by design, so its silence proves nothing, and still not exempt), it asks each session still holding it — the worker, and a reviewer or verifier whose result is not on the ticket after its start — whether it is alive, through that session's own runner's `liveness` and no other runner's, and only when the session's `*.started` names this machine (`machine`, the hostname) — a session started on another machine is recorded as `unknown` and reported, never asked: `alive` does nothing; `stopped` posts `worker.lost`, `reviewer.lost` or `verifier.lost` naming that (runner, session); `unknown` is recorded in the heartbeat and reported, never taken for alive and never a `*.lost`. A held ticket silent for `--idle` seconds (default 3600) whose worker's runner answers `alive` and that waits on nothing — no live reviewer or verifier, no product slot, no pass — is a finding too: that worker ended its turn with nothing to wake it. What it finds besides a stopped session — the relay down, a runner that could not say or a session on another machine, a held ticket with no session to ask, such an idle worker, events that cannot be read, the board unread past its tolerance — it sends itself, through the `send` of the runner the main agent runs in: a finding about a ticket to the main agent of that ticket's watch, `relay down` and the unread board to every watch's main agent, one line whose findings each begin `watchdog:`, each finding once: not a wake, not a row of the wake queue, never acked. A send that started a turn ends it, and that turn's end re-arms it through the **turn guard**. `watchdog.py arm` starts it unless it is healthy; `status` prints the heartbeat.
_Avoid_: watcher, heartbeat (for the process), board.py, judge (as a name for the script)
_Home_: `mmw-v2/skills/dispatch/scripts/watchdog.py`

**heartbeat**:
`watchdog.json` in the state directory: what the **watchdog** writes at start, after every ticket and at the end of every round — its `pid` and process `identity`, `at`, `poll`, `tolerance`, `silence`, `idle`, the watches it read, the tickets `held` and `waiting` at its last round (`held` is null when that round could not read every ticket), the sessions whose runner answered `unknown`, the `*.lost` it posted, the relay's problem if any, and the findings `pending` and `reported`. The watchdog is **healthy** when its `watchdog.lock` names a live process by pid and identity, that same process wrote the heartbeat, and the heartbeat is no older than its **tolerance**. A heartbeat another process wrote proves nothing about the one holding the lock.
_Avoid_: `mmw-night-<spec>`, beat (for this file; the relay's `beat.json` is its last good poll)
_Home_: `mmw-v2/skills/dispatch/scripts/watchdog.py`

**tolerance**:
How old a heartbeat may be and still be fresh, and how long the board may go unread: `max(300, poll + margin)` seconds, the margin being one adapter call plus one gh read (60 + 120), the longest a watchdog waits between two beats. A fixed number would read a healthy watchdog as dead mid-sleep as soon as its poll grew past it, and a smaller margin would have `arm` end one that is only slow. For a runner, the tolerance of a `stopped` answer is how long a dead session may still read `alive`; the Herdr adapter records its measured value (1 second) in its header.
_Home_: `mmw-v2/skills/dispatch/scripts/watchdog.py`

**turn guard**:
`scripts/turn-guard.py` of the dispatch skill, the first layer of liveness: a hook `install.sh` registers on the turn-end event of all five hosts (`Stop` for Claude, Codex and Grok, `stop` for Cursor, `agent_settled` through an extension for Pi). It acts only in a session that is the main agent of an open watch in `watches.json`: that watch's runner's `self` must answer this session's id, and anything it cannot establish — no watch, no adapter, a `self` that cannot answer — means it is not a main agent and nothing is held. It arms the **watchdog** when it is not healthy and, when tickets are held and the watchdog still is not healthy, keeps the turn from ending — exit 2 on Claude, Codex and Grok; one follow-up message on Cursor and Pi, which cannot hold a turn — once per turn end, with the one command to run. The copy registered for Claude stands down when `GROK_AGENT` or `GROK_HOOK_EVENT` is set and when the payload carries Cursor's `cursor_version`, and never on `GROK_SESSION_ID`; the copy registered for Cursor acts only on a payload with `cursor_version`. Every decision it makes is appended to `guard.log` in the state directory. What each host was seen to do is recorded in the script's header.
_Avoid_: stop hook (as its name), turnend guard, auto-arm
_Home_: `mmw-v2/skills/dispatch/scripts/turn-guard.py`

### Working discipline

**narrowed reading**:
The worker's reading at start of work: the ticket in full including comments; every `## Read first` item to its conclusion; along `## Parent`, only the `## Implementation Decisions` subsections it names plus `## Testing Decisions` and `## Out of Scope`, never the whole spec; then `CONTEXT.md`. Code review's spec-source step reads the same way.
_Avoid_: 读法收窄, 只读指名小节
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**state the seam**:
The last step before writing code: one sentence naming which layer, which directory, and which precedent to copy, taken from `## Seam`; when the ticket has no such section, derived from `## Testing Decisions` and commented on the ticket first.
_Avoid_: 说出 Seam
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**writing rules**:
The While writing code section of `implement`, between stating the seam and `Use /tdd`: the baseline is the contract (`--sub-issue contract` when it does not fit); `Put no question on the screen` — take the default and record it under `Decisions I made on my own`; before changing a function, grep every caller and fix the shared place; before adding a branch or guard, name and delete the one it makes redundant; before writing a helper, look for one in the repository and `## Read first`; before adding a file, dependency, or configuration, say why the existing one is not enough; never simplify away security, data-loss prevention, accessibility, or what the ticket explicitly asks for (`## What to build`, every criterion, the baselines, the Seam interface); Owns two grades (`--sub-issue deferred` for a convenient change).
_Admitted_: While writing code
_Avoid_: 写码纪律, 写码纪律七条, the seven working rules, 不问 (as a name)
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**closing steps**:
What `implement` does once the code is written: the worker's own run (`<engine> <n>`); start the reviewer (`<dispatch> start <n> reviewer`), fix in-ticket findings for one round, `--sub-issue finding` for the out-of-ticket ones, no re-review; `--decisions`; start the verifier (`<dispatch> start <n> verifier`) once, since `--closeout` requires its verdict to cover `HEAD` and every earlier step still writes commits; `Audit`; `--touched`; `--sub-issue decision` for criteria that only wait for a person's one sentence, then `--draft` and fill the two placeholders; `--closeout`. `--closeout` archives no agent: landing does that, and takes the workspace with the agents inside it (`land <n>` for one ticket, `advance` for a batch). A resumed worker resumes at the step `implement`'s resume table gives for the `ticket.checked` events and the `reviewer.reported`, `worker.decided`, `verifier.passed` and `verifier.failed` events on the ticket. No branch is pushed and no pull request is opened: work reaches the base branch through `land` or `advance`.
_Avoid_: 收尾七步, 收尾六步, the seven closing steps, the closeout (for the sequence)
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`Audit`**:
The closing step that re-reads the whole ticket and every `## Read first` item, traces every criterion to its latest `EVIDENCE:`, and recounts `Counts:`.
_Avoid_: 交接前自审
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**closeout**:
`verify-ticket.py <n> --closeout <draft>`, the closing gate — the only place in the pipeline that closes a ticket or changes its queue label while it is being worked. It checks the draft against the ticket and the repository (first line, kinds, evidence behind every tick, `Counts:` agreeing with the first line, the newest reverify `ticket.checked` with result `met`, that run covering the criteria the ticket now states, a `verifier.passed` or `verifier.failed` event whose `commit` is `HEAD`, no unreadable event on the ticket, no uncommitted tracked changes and the branch containing its base commit). It also gives the claim back, in the same edit that takes `ready-for-agent` off. A draft that fails those conditions changes nothing, names the condition on stderr, and exits 1; the worker fixes the draft or the ticket and runs again. After an `ALL MET` draft is accepted it then runs `.mmw/target.json`'s optional `checks` and posts them as a `ticket.checked` of run `repo-checks`; an `unmet` one leaves the ticket open. On success it removes `ready-for-agent`, closes the ticket (`gh issue close --reason completed`, `CLOSED: #<n>`), and then posts the comment as `ticket.passed`; on `HANDOFF REQUIRED` it hands the ticket back, leaves it open, gives back the product slot its worktree holds, if any, and then posts the comment as `ticket.returned`. It archives no agent. `--check-only` is the dry run, printing `CLOSEOUT OK: #<n> draft passes every check`, and does not run `checks`. A command that would bypass it is refused by `hook.py`.
_Admitted_: closing gate
_Avoid_: 关票门, the gate at the end, 关票 (as a term)
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**host neutrality**:
A skill's text is one and the same for every host: no host is the default or preferred, nothing branches on a host's name, and differences in capability are written as natural language that judges by capability. The five hosts: `claude`, `codex`, `grok`, `cursor`, `pi`.
_Avoid_: 五宿主平权, host-neutral (as a name), 五个宿主
_Home_: `AGENTS.md`

**runner neutrality**:
A skill's text is one and the same for every runner: nothing branches on a runner's name, and a difference in what runners can do is written as that capability. Which runner runs tonight is chosen by `models.py runner`, whose last step is a default; the text states that choice and assumes nothing past it. A runner's own commands are written only in its adapter. A skill's `description` names no runner, since every host scans it into its system prompt: a runner that cannot start is refused by one stderr line of the script at run time, never by a precondition in the `description`.
_Avoid_: runner-neutral (as a name)
_Home_: `AGENTS.md`

**skills called by name**:
A skill's scripts are resolved by the agent holding that skill, from its own `SKILL.md`, as `scripts/…`; a caller names the skill and what it wants done, never an install path. Installing a skill is receiving its scripts, so the two cannot drift and the path is right on every host. The `CHECK:` written into a ticket is run by a shell with no agent in between, and it names no path either: `verify-ticket.py` resolves the drive-target skill's `scripts/` through `--tools` and puts it on that shell's `PATH`.
_Home_: `AGENTS.md`

**silence is never a pass**:
The question a gate is judged by when it is added or changed: *if this ran and did nothing at all, would anyone find out?* A gate that neither does its job nor says so reads exactly like one that passed, so everything here that can refuse names the fact it checked, gives the one way out, and fails loudly when it could not run at all. The three-part shape of a refusal message itself is `refusal.py`.
_Avoid_: 沉默不算通过, fail-safe (for this)
_Home_: `docs/adr/0008-silence-is-never-a-pass.md`

**the ticket is the only state**:
Every run reads the ticket afresh, writes its events there, and carries nothing to the next run but what they say; the ledger is thrown away; the ticket body is never edited — run state lives in the comments, and where a ticket stands is their fold. `status.py` keeps no state file for the same reason. The relay's state directory holds only what the relay has to deliver — wake-up rows, acks, its marks on each ticket — and never a ticket's state.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**The environment is yours; the repository is not**:
The verifier may install a dependency, download a browser, or find a connection string, and leaves the repository exactly as it found it; two identical `git status` outputs are the proof. What it never repairs is what the machine hands out: ports and the data directory come from the lease, and the product is started and stopped only by `.mmw/target.json`'s own commands, which the criteria run themselves.
_Avoid_: the verifier's boundary
_Home_: `mmw-v2/skills/verdict/SKILL.md`

**No pull request**:
No step of the pipeline reads a pull request. Ticket branches are pushed to origin for cross-machine handoff; a ticket's work still reaches the base branch through `advance`'s local merge, and the closing comment's `PR:` line is written in the future tense.
_Home_: `mmw-v2/merge-notes/implement.md`

**fixed headings**:
A section of tracker text that a downstream reader finds by position keeps a fixed heading: the producer fixes the literal, the reader cites the same literal. `implement` reads a ticket by `## Read first`, `## Seam`, `## Owns` and a spec by `## Sources`; renaming one means changing `implement` too.
_Avoid_: 节名 (as a term)
_Home_: `docs/adr/0001-tracker-repo-authority.md`

**no implementation file paths**:
A spec names no implementation file paths but must name source paths, test directories, and shared contract locations; a ticket's two exceptions are the Seam's test directory or file and the `## Owns` paths.
_Avoid_: 路径禁令
_Home_: `mmw-v2/merge-notes/to-spec.md`

**skills are deliverables**:
The skills in this repository are what it ships, not the working instructions of an agent working on this repository.
_Home_: `AGENTS.md`

### The toolbox

**skill**:
The unit the toolbox ships, one directory with a `SKILL.md`. This repository's own: `dispatch`, `verify-ticket`, `verdict`, `advisor`, `drive-target`, `align-screens`, `exe-release`, `manage-agents-md`, `claude-design-blocks`, `code-checkers`. From `mattpocock/skills`: `to-spec`, `to-tickets`, `implement`, `code-review`, `triage`, `wayfinder`, `domain-modeling`, `grilling`, `grill-me`, `grill-with-docs`, `prototype`, `research`, `resolving-merge-conflicts`, `setup-matt-pocock-skills`, `codebase-design`, `improve-codebase-architecture`, `tdd`, `diagnosing-bugs`, `ask-matt`, `wait-what`, `teach`, `to-questionnaire`, `writing-for-agents`, `handoff`, `wizard`. From `cathrynlavery/diagram-design`: `diagram-design`. A skill is named by its directory name; `the X skill` in prose, never `/X`.
_Home_: `mmw-v2/skills.txt`

**`SKILL.md`**:
A skill's entry file: the host loads the skill from it, and its location resolves the skill's `scripts/` and `references/`. It is symlinked from the source directory, so an edit takes effect on the next invocation; only its frontmatter **`description`** — the one thing a host scans at start — needs a new session. The frontmatter switch **`disable-model-invocation`** makes a skill user-invoked only; it is set or removed together with `policy.allow_implicit_invocation: false` in `agents/openai.yaml`, and this repository keeps it only on `setup-matt-pocock-skills`, `grill-me`, `handoff`, `wait-what`. A step in a skill closes with **`Done when`**, its completion test.
_Avoid_: 技能正文 (as a term), 用户触发开关, user-invoked (as a name), completion criterion
_Home_: `AGENTS.md`

**`skills.txt`**:
The one list deciding which skills are installed: `<root>/<name>` lines under `self/`, `engineering/`, `productivity/`, `dd/`; `install.sh` reads it.
_Avoid_: 名单 (as a term)
_Home_: `mmw-v2/install.sh`

**`tests/run.sh`**:
Each skill's test entry point, the own-script layer; run by hand — there is no CI.
_Home_: `AGENTS.md`

**merge-note**:
One note per changed upstream skill in `mmw-v2/merge-notes/`: which passages this repository changed, why, and how to choose when upstream touches them again — intent, not diff. Its fixed parts are Chinese literals: `源目录：`, `## 逐段意图`, the table columns `段落` and `我们的意图`, `收上游` and `弃上游`. `merge-notes/README.md` indexes them and gives the upstream-pull procedure; gate-check has `UPSTREAM.md` instead.
_Admitted_: 说明 (in `merge-notes/README.md`)
_Home_: `mmw-v2/merge-notes/README.md`

**downstream-note**:
One note per change in this repository that invalidates a consuming repository's existing screen contract, ticket `CHECK:`, or `.mmw/target.json` — what changed, which of those classes (plus target trees) go stale, and how to migrate — the opposite of a merge-note; `mmw-v2/downstream-notes/README.md` says which changes require one. Its fixed parts are Chinese literals: `## 改了什么`, `## 哪些产物失效`, `## 怎么迁`.
_Admitted_: 说明 (in `downstream-notes/README.md`)
_Home_: `mmw-v2/downstream-notes/README.md`

**`UPSTREAM.md`**:
The note written whenever upstream scripts are copied in without a subtree: source repository, commit, date, and which lines were changed.
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`

**`models.md`**:
The live table at `~/.mmw/models.md`, one row per agent — a second row for the same agent is refused when the table is read. Four columns `agent | host | model | effort`, everyday names, for every agent the pipeline sends out except the main agent and the three code-review axis subagents — the only place a dispatched agent's model is written. A two-cell `| runner | <name> |` row may sit above them: the live table's say in which runner runs tonight, below `MMW_RUNNER` and above runtime detection. `start` asks this machine what that host offers and uses the unique match; it reads only the rows above `<!-- mmw-offerings -->`. Below that marker is this machine's last scan of the five CLI hosts, written by `python3 models.py offerings` and refreshed by a later `install.sh`; `start` does not read it. `models.py` next to `hosts.json` is the only reader of the rows. Git holds no human-edited copy: `hosts.json` records how each host starts — its own command-line flags, which every runner that runs the host's CLI in a terminal uses, and its settings on Paseo — plus the default rows first `install.sh` copies here. The three code-review axis subagents have no row of their own: they run on the model of the reviewer session that starts them. An agent told to change host, model, `effort`, or tonight's runner reads `references/editing-models.md`.
_Avoid_: the table (for this), 模型表, 角色表, launch arguments
_Home_: `~/.mmw/models.md`

**`effort`**:
The `effort` column of the live table: the everyday thinking level (`high`, `xhigh`, `medium`, …). Grok, Claude, Codex and pi take it as a flag or thinking option. Cursor does not: effort is set per model in the Cursor app, and `start` only selects among the pairs `cursor-agent models` already lists. Where the host takes it, a runner that runs the host's own CLI passes it as that CLI's flag from `hosts.json`; on Paseo it becomes the `--thinking` value of `paseo run`, which for Cursor is only on or off. Every row needs one.
_Admitted_: thinking level
_Avoid_: thinking effort, reasoning effort (in prose), 思考强度
_Home_: `~/.mmw/models.md`

**permissions**:
How a dispatched session is started: all tools granted. It is not a column of the live table. Each host's spelling lives in `hosts.json` (`bypassPermissions`, Cursor `auto_accept`, …). There is no read-only value: no host has a mode that both keeps a session to reading and lets it finish a turn on its own, so an agent that must not write is a subagent, held to reading by what it is told to do and by whatever restriction the call that starts it can carry.
_Avoid_: launch arguments
_Home_: `mmw-v2/skills/dispatch/hosts.json`

**`models.py`**:
`mmw-v2/skills/dispatch/scripts/models.py`, the only reader of the live table and of `hosts.json`. It resolves everyday names against tonight's catalog and turns a row into the flags a runner starts the host with, so `install.sh --check` and `dispatch.sh start` cannot disagree about it. `python3 models.py offerings` asks the five CLI hosts and writes the catalog under the live table; `start` does not read that block.
_Home_: `mmw-v2/skills/dispatch/scripts/models.py`

**`install.sh`**:
`mmw-v2/install.sh`, the only install entry. It installs seven things: skill symlinks into `~/.agents/skills` and `~/.claude/skills`; hooks into each host's own configuration; user-level prompts (`~/.claude/CLAUDE.md` a symlink to `prompt/shared.md`, Codex, Pi and Grok each a file `prompt/render.py` writes); a launchd task that re-renders those three when the source changes; Paseo configuration (`~/.local/bin/paseo`, two providers in `~/.paseo/config.json`, `worktrees.root`); Orca worktree configuration, only where `orca` is installed (every Orca setup's `worktree-base-path` is `.worktrees`, and `--check` also wants each repository's external worktrees shown); the `nowledge-mem` entry in `~/.cursor/mcp.json`. It does not write Agent profiles; leftover generated profiles (notes containing `from models.md`) are reported as `残留`. First install copies the live table if it is missing; later ones leave the rows and refresh the CLI catalog below them. It reads `skills.txt`, clears the retired locations, and prints one line per item with the prefixes `已装`, `残留`, `退役`, `冲突`, ending with markers such as `HOOKS-INSTALLED`. **`install.sh --check`** looks and changes nothing: exit 0 when complete, 1 when something is missing or a stale link remains; it expands every live-table row through `models.py`, holds each runner adapter's `# MMW_USES:` lines against the binary on `PATH` — printing `没查` when it could not read what the binary accepts and `不一致` when a command or flag is gone, never one for the other — and `dispatch.sh check` runs it before a night. `MMW_V2_HOME` moves the install location for tests.
_Avoid_: the installer, 安装器, 安装入口 (as a term), 只看不动 (as a term)
_Home_: `mmw-v2/install.sh`

**`--tools`**:
The one flag `verify-ticket.py`, `dispatch.sh` and `lint_contract.py` share: a directory holding the scripts of another skill (the drive-target skill's `scripts/`, the verify-ticket skill's for `dispatch.sh`), repeatable. For `verify-ticket.py` and `dispatch.sh` it is an override: each resolves its sibling skill's `scripts/` from its own location, and uses what `--tools` gives instead when it is given. `verify-ticket.py` puts the directories in force on the `PATH` of every `CHECK:`, so a criterion names a judge bare and carries no install location; `dispatch.sh advance` passes them on to the `start` it runs. For `lint_contract.py` it stays required: missing, that script exits 2 and prints its usage.
_Avoid_: tools dir, 工具目录 (as a term), skills root
_Home_: `mmw-v2/skills/drive-target/SKILL.md`

**hook**:
A program a host runs at an event. This repository installs `hook.py` (`pretool` on every host, `question` on the session hosts), registered in the host's configuration, with a **matcher** (the tool pattern) where the event takes one.
_Avoid_: 钩子 (for this sense), turn.py
_Home_: `mmw-v2/install.sh`

**`hook.py`**:
`scripts/hook.py` of the drive-target skill, the host-side enforcement of two rules, one per member of its `GATES`: **`pretool`** — when the host is about to run a shell command, it refuses `gh issue close` and label changes on the ticket named by the working directory's basename `issue-<n>`, checks nothing, and points at `--closeout`; **`question`** — when the host is about to call its question tool in a ticket worktree, it refuses and names the two ways out. A cwd that is not `issue-<n>` is not a gate of either kind; a host that runs its hooks from elsewhere (Cursor runs them from `~/.cursor`) is placed by `PASEO_AGENT_CWD` instead, which only a Paseo agent has. Its answer takes each host's shape (`permissionDecision: deny` on Claude Code and Codex, `decision: deny` on Grok, which clips the reason at 256 characters, `permission: deny` on Cursor); the verb in prose is **refuse**. It is symlinked, so editing it needs no reinstall.
_Admitted_: hook.py pretool
_Avoid_: the pretool gate, pretool 门, 关票 gate, 拦截 hook, MMW_TICKET, MMW_AUTONOMOUS
_Home_: `mmw-v2/skills/drive-target/scripts/hook.py`

**`rule-at-moment.py`**:
`mmw-v2/hooks/rule-at-moment.py`, a Claude Code hook kept in the repository but not installed by `install.sh` (registered by hand as `~/.claude/hooks/rule-at-moment.py` if wanted): at the moment a ground rule of `~/.claude/CLAUDE.md` applies, it puts that rule's own text in front of the model — the file size before a `Read`, the next `offset` after a truncated one, rules 1, 3, 4, 6, 7 before a write, and rule 6 before an `Agent` call.
_Avoid_: 规则提醒 hook, 注入 hook
_Home_: `mmw-v2/hooks/rule-at-moment.py`

**`verify-ticket.py`**:
`scripts/verify-ticket.py` of the verify-ticket skill — one script carrying eleven jobs: `--lint`, the worker's own run `<n>`, `--reverify` (the verifier's, or the main agent's with `--actor main`), `--preflight`, `--closeout <draft>` (with `--check-only`; `--timeout <seconds>` raises the per-`CHECK:` limit for one run, and `TIMEOUT:` lines on the ticket raise it for every run), `--decisions <file>`, `--touched`, `--draft <out-file>`, `--sub-issue <kind> <file>`, the reviewer's `--review <file>`, the verifier's `--verdict "<one line>" --model <model>`. It is the only route by which a ticket closes; it reads the `<issue-template>` shape; `--jobs` stays 1 because the branch, the ticket, and the working tree are shared. Exit 0, or 1 when `--closeout` refuses or `--sub-issue` opened the child but could not write its `child.opened`, or 2 when `--preflight`, `--decisions`, `--touched`, `--sub-issue`, `--review` or `--verdict` refuses. The two runs of the criteria also exit 3 when they waited for a product slot and none came free, and 4 when the `ticket.checked` recording them could not be written. The skill's own text calls it `<engine>`.
_Avoid_: the engine, the ticket script, the script (for this)
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**--decisions**:
`verify-ticket.py <n> --decisions <file>`: checks the file has the two sections `Decisions I made on my own` and `Outside Owns` and that `Outside Owns` matches the newest `ticket.checked` of run `self`, then posts it as the `worker.decided` event, first line `DECISIONS`. Exit 2 and nothing posted if the ticket already carries a `worker.decided` event or the file is missing a section.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**--touched**:
`verify-ticket.py <n> --touched`: reads the `Outside Owns:` files of the newest `ticket.checked` of run `self` and posts a `worker.touched` event on each open sibling whose `## Owns` covers one of them. Exit 2 if there is no `reviewer.reported` event. No such file: nothing posted, exit 0.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**--draft**:
`verify-ticket.py <n> --draft <out-file>`: writes the closing-comment skeleton to `<out-file>`, with `skipped:` and `Decisions I made on my own` left as `<fill>`. Nothing lands on the ticket. `--closeout` refuses the skeleton until those are filled.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**--sub-issue**:
`verify-ticket.py <n> --sub-issue <kind> <file>`: opens a new issue labelled `needs-triage` and `mmw:child`, parented to this ticket, its body's first line ``A `<kind>` child of #<n>.``, and posts `child.opened` on this ticket. `kind` is one of the five child kinds: `finding`, `contract`, `deferred`, `decision`, `fault`. Empty file, unknown kind, or a `mmw:child` label the repository lacks and will not let be created: exit 2. Exit 1: the child is open and its `child.opened` could not be written, so opening it again would make two.
_Home_: `mmw-v2/skills/verify-ticket/references/sub-issues.md`

**`tree.py`**:
`scripts/tree.py` of the verify-ticket skill: the tree under a map, a spec or a ticket read in one GraphQL query, at fixed page sizes — 50 specs under a map, 100 tickets under a spec, 50 children under a ticket — each issue with its number, title and state, and each issue with a layer below it with GitHub's count of that layer. `status.py` and `--lint` read a spec's batch through it. A list shorter than the count GitHub gives for it, or an answer carrying `errors`, is refused (exit 2) rather than read as the whole: a page left unread raises no error of its own.
_Avoid_: sub_issues endpoint (for reading a tree), tree walk
_Home_: `docs/agents/issue-tracker.md`

**ADR**:
An architecture decision record in `docs/adr/`, `0001-slug.md`, numbered current highest plus one. Its shape here: `date` and `amends` frontmatter, a one-line `# ` heading that is the decision itself, a paragraph of prose under it, zero to two freely titled sections, `## Considered Options`, `## Consequences`. `docs/adr/README.md` is the hand-kept index, with the columns `改写了哪几份` and `被哪几份改写` for the amend relation and a translation table for the two earlier numberings. An ADR's decision — its `# ` heading and the prose under it — is a baseline source.
_Home_: `docs/adr/README.md`

**research file**:
The Markdown file with citations the `research` skill leaves in the repository; one of the nine `## Sources` kinds; read to its last section as a `## Read first` item; its body is working material, not a baseline. `wayfinder:research` is the matching decision-ticket type.
_Home_: `mmw-v2/upstream/skills/engineering/research/SKILL.md`

### Values at a glance

| name | values |
| --- | --- |
| event | `spec.opened` · `spec.suspended` · `spec.closed` · `ticket.claimed` · `ticket.refused` · `ticket.passed` · `ticket.returned` · `ticket.released` · `ticket.landed` · `ticket.regressed` · `ticket.checked` · `worker.started` · `worker.resumed` · `worker.retracted` · `worker.replaced` · `worker.decided` · `worker.queued` · `worker.touched` · `worker.lost` · `reviewer.started` · `reviewer.reported` · `reviewer.lost` · `verifier.started` · `verifier.passed` · `verifier.failed` · `verifier.lost` · `child.opened` · `child.closed` |
| event subject | `spec` · `ticket` · `worker` · `reviewer` · `verifier` · `child` |
| common payload field | `v` · `event` · `stage` · `actor` · `spec` · `ticket` · `at` |
| ends every hold | `ticket.landed` · `ticket.returned` · `ticket.released` · `spec.suspended` |
| ends one session's hold | `worker.retracted` · `worker.lost` · `worker.replaced` · `reviewer.lost` · `verifier.lost` · `ticket.refused` (naming its session) |
| gives the product slot back (`SLOT_ENDS`) | `ticket.landed` · `ticket.returned` · `ticket.released` · `spec.suspended` · `worker.retracted` |
| `ticket.refused` reason | `wrong-branch` · `dirty-tree` · `not-open` · `not-ready` · `blocked` · `claimed-by-other` |
| `ticket.released` reason | `landed` · `suspended` · `worker-lost` |
| `child.opened` kind | `finding` · `contract` · `deferred` · `decision` · `fault` |
| `child.closed` resolution | `fixed` · `stale` · `became-ticket` |
| `ticket.checked` run | `self` · `reverify` · `repo-checks` |
| `ticket.checked` result | `met` · `unmet` · `handoff` |
| `worker.queued` reason | `product-full` · `machine-full` |
| `phase` | the newest event's name · `closed` · `-` |
| `status.py` columns | `ticket` · `runner` · `session` · `worker` · `since` · `phase` · `ac` · `note` |
| `note` | `ready` · `waiting on #<m>` · `(passed, not landed)` after a blocker · `<k> live workers: …` · `events unreadable: …` · `claimed, no session started yet` · `waiting for a product slot since <time> (<reason>, <k> of <max> held)` · newest event's first line · empty while a worker holds it |
| relay wakes the worker | `reviewer.reported` · `verifier.passed` · `verifier.failed` · `reviewer.lost` · `verifier.lost` · `worker.queued` (a slot given back) |
| watchdog finding | `relay down` · `liveness unknown` (the runner could not say, or the session was started on another machine) · `held with no session to ask` · `silent … with nothing to wait on` (an idle worker) · `events unreadable` · `cannot read the board` |
| ends the hold of the session that produced it | `reviewer.reported` · `verifier.passed` · `verifier.failed` |
| turn-end event (turn guard) | Claude, Codex, Grok `Stop` (exit 2 holds the turn) · Cursor `stop` (`followup_message`) · Pi `agent_settled` (follow-up) |
| relay wakes the main agent of the ticket's watch | `ticket.passed` · `ticket.returned` · `ticket.refused` · `child.opened` (kind `fault` or `decision`) · `worker.lost` · `relay.recovered` |
| relay send answer | `0` delivered · `4` handed over, unconfirmed (treated as delivered) · `3` nothing sent · `2` no such session · other kept |
| finish notification | `finished` · `errored` · `was closed` · `needs permission` |
| host | `claude` · `codex` · `grok` · `cursor` · `pi` |
| runner (one adapter each) | `paseo` · `orca` · `herdr` |
| adapter verb | `start` · `send` · `liveness` · `stop` · `self` |
| `liveness` answer | `alive` · `stopped` · `unknown` |
| `target.kind` | `electron` · `web-spa` · `web-server-rendered` · `chrome-extension` |
| mechanism `via` | `api` · `storage` |
| worker grade | `junior-worker` · `senior-worker` |
| `ABANDON:` kind | `failed` · `stuck` · `decision` |
| `ready-for-human` kind | `reaction` · `reach` |
| criterion state | `met` · `unmet` · `abandoned` |
| gate-check status line | `RUN` · `PASS` · `FAIL` |
| lint level | `ERROR` · `WARN` |
| advance plan line | `MERGE <n>` · `RELEASE <n>` · `DISPATCH <n>` |
| lease environment | `MMW_INSTANCE` · `MMW_SLOT` · `MMW_PORT_BASE` · `MMW_PORT_COUNT` · `MMW_DATA_DIR` · `MMW_AUTOMATION` |
| `hook.py` gate | `pretool` · `question` |
| layer label | `mmw:map` · `mmw:spec` · `mmw:ticket` · `mmw:child` |
| state role | `needs-triage` · `needs-info` · `ready-for-agent` · `ready-for-human` · `wontfix` |
| category role | `bug` · `enhancement` |
| `dispatch.sh` constants | `MERGE_TRIES = 3` · `LABEL_TITLE_CHARS` · `DEFAULT_WORKER` |
| `lease.py` constants | `MMW_LEASE_SLOTS = 8` · `MMW_LEASE_PORT_BASE = 21000` · `MMW_LEASE_PORT_STRIDE = 20` |
| `dispatch.sh` verbs | `check` · `open` · `open-ticket` · `adopt` · `self` · `advance` · `land` · `start` · `retract` · `wait` · `ack` · `resume` · `status` · `reverify` · `route` · `summary` · `suspend` |
| `relay.py` verbs | `run` · `start` · `add` · `stop` · `watching` · `ack` · `queue` |
