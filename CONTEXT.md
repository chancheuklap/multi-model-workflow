# Multi-Model Workflow

A toolbox of skills and subagents shared across hosts, repositories, and machines. Its core is the landing pipeline: one unit of work travels from a written spec, through a ticket, through an agent that writes the code, to a closed ticket with evidence attached. This file fixes the name of everything the pipeline invents, so that a session starting with an empty context uses the same word the last one used.

How to read an entry: the bold line is the term's only name; a term whose name is a literal string that appears in a file, a command, or a comment is named by that string exactly (case, colon, and all). The definition says what the thing is and what sets it apart from its neighbours. `_Admitted_` lists the one other wording that may appear in prose. `_Avoid_` lists dead words: a sentence in this repository that uses one is wrong; an item followed by a note in parentheses says in which sense the word is dead. `_Home_` is the file whose text or code the definition is taken from; when this file and that one disagree, that one is right and this file is rewritten.

Vocabulary that belongs to one skill alone — `exe-release`'s release key, tiers, build machine and hooks; `claude-design-blocks`'s page kinds and helpers; `manage-agents-md`'s survey entries; the design vocabulary of upstream skills such as `codebase-design` — is defined in that skill's own files and is not repeated here.

## Language

### Roles

**agent**:
Any session or subagent this pipeline sends out or runs: the main agent, a worker, a reviewer, the verifier, the advisor, the claim-checker, the board.
_Home_: `mmw-v2/skills/dispatch/models.md`

**session**:
A host process started through Herdr in a pane of its own. It carries a host, a pane, pane tokens, and — for a worker only — `MMW_TICKET`. The main agent, a worker, and a reviewer are sessions; the verifier and the three code-review subagents are subagents inside a session.
_Avoid_: 会话 (as a term)
_Home_: `mmw-v2/skills/dispatch/models.md`

**main agent**:
The session the user started themselves. By day it works with the user to produce specs and tickets; by night it runs `dispatch.sh run` and `dispatch.sh advance` and only reads tickets. It is the one agent with no row in `models.md`; its pane is named `mmw-main`; it carries no `MMW_TICKET`; it is tied to no host.
_Avoid_: coordinator, orchestrator, 编排者, 主 agent, 出票的主 agent, 落地 agent, the single Claude Code session
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**worker**:
An independent session dispatched to do one ticket, running the whole path from claiming the ticket to writing the closing comment. It runs the `implement` skill; its only input is the ticket; it owns the `issue-<n>` worktree and branch; it carries `MMW_TICKET` and the pane token `kind=worker`; it dispatches its verifier and starts its reviewer; it never closes the ticket by hand.
_Admitted_: worker session
_Avoid_: 工人, 做票的 agent, 领票的 agent
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**worker grade**:
Which of the two workers a ticket goes to. Each grade is at once a ticket label, a row of `models.md`, and the answer in the ticket's `## Worker` section; the user sees it once, as the `Worker:` line of the `to-tickets` quiz, and the label is read afresh every time the ticket is started.
_Avoid_: grade of worker, seat, lane (for this)
_Home_: `mmw-v2/skills/dispatch/models.md`

**`junior-worker`**:
The default worker grade (`DEFAULT_WORKER` in `dispatch.sh`).
_Avoid_: 初级工人, 初级 worker
_Home_: `mmw-v2/skills/dispatch/models.md`

**`senior-worker`**:
The worker grade a ticket names when getting it wrong would be wrong silently.
_Avoid_: 高级工人, 高级 worker
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**reviewer**:
The session a worker starts through the dispatch skill to run one round of code review. Its Herdr name is `issue-<n>-review`; it runs inside the worker's worktree, cuts no branch, carries `MMW_AUTONOMOUS` but no `MMW_TICKET`; the board never touches it; the worker closes its pane right before the closeout, because after the closeout the board closes the worker's own pane at once. On its own, `reviewer` always means this session, never one of the three axis subagents.
_Admitted_: reviewer session
_Avoid_: reviewer 会话, code-review 会话, 审稿人
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**dispatcher**:
The role the reviewer session takes once it holds the `code-review` skill: it starts the three read-only axis subagents, sorts every review finding into in-ticket or out-of-ticket by the five conditions in that skill's section 3, and writes the one review comment. It reviews nothing and fixes nothing itself, and it is the only reader of `code-review/SKILL.md`.
_Avoid_: 派发 (as a term)者
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**verifier**:
The subagent a worker dispatches once, with the prompt `verify #<n>` and nothing else. In the same worktree on the same commit it re-runs every acceptance criterion with `--reverify` and posts one `VERDICT`. It may repair its environment and changes no file in the repository; it never writes an `ABANDON:` line.
_Avoid_: 复验者, verifier 子代理, subagent verifier
_Home_: `mmw-v2/agents/verifier/body.md`

**advisor**:
The subagent that gives a second opinion on a stronger model; read-only, it implements nothing.
_Home_: `mmw-v2/agents/advisor/body.md`

**claim-checker**:
The subagent that fact-checks a finished document and returns a claim table — every claim marked ✅ sourced, ❌ unsourced, or ⚠️ misleading, with a severity. The `readable-docs` skill runs it before a document is saved or published.
_Avoid_: the checker (for this), claim checker
_Home_: `mmw-v2/agents/claim-checker/body.md`

**board**:
The agent resident in one Herdr workspace for the night. It reads each worker's `turn` pane token and does one of three things — sends `continue` to a worker whose turn failed, tells `mmw-main` about a worker that stopped on its own (`STOPPED`) or held a ticket past `MAX_HOURS` (`TIME LIMIT`), closes the pane of one at `phase=closed` or `phase=handoff` — announces the frontier with the `mmw board:` line, and writes the `NIGHT SUMMARY`. It keeps no state file: its two sources are the issue tracker and Herdr. It changes no label, starts no session, and reads no screen; every decision is the main agent's.
_Admitted_: night board
_Avoid_: the night's agent
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**host**:
The command-line agent program a session runs on: one of `claude`, `codex`, `grok`, `cursor`, `pi`. It is the `host` column of `models.md`; Herdr calls it the agent kind. Each host has its own install locations, hook configuration, form close key, and effort spelling.
_Admitted_: agent kind (when speaking of Herdr)
_Avoid_: 宿主
_Home_: `mmw-v2/skills/verify-ticket/scripts/hook.py`

**user**:
The person. By day they work with the main agent on specs and tickets; they are the only reader of a `ready-for-human` ticket; `needs-triage` and `needs-info` wait on them; they are told when the night is over.
_Avoid_: human (for this), maintainer (in this repository's text), reporter (in this repository's text), 用户 (as a term)
_Home_: `docs/agents/triage-labels.md`

**subagent**:
An agent started inside a session rather than through Herdr. As a deliverable it is one of the two things the toolbox ships: one shared `body.md` wrapped in a per-host shell by `assemble.py` into `agents/<name>/out/` and symlinked once per host, a `models.md` row whose launch arguments are `—`. The verifier is a subagent of the worker's session; the three code-review axis subagents are the `reviewer` subagent inside the reviewer session, built from the same `models.md` reviewer row that starts the session.
_Avoid_: sub-agent, background agent, seat, 子代理 (as a term)
_Home_: `mmw-v2/install.sh`

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
The outside repository where real tickets are run, as distinct from the toolbox. It must hold a `DESIGN.md` before UI refinement; `models.md` is never placed in it.
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
The host-neutral install location `install.sh` creates on every machine; Codex, Cursor, Grok, and Pi scan it. `~/.claude/skills` is the second copy, because Claude Code scans only that. Both hold symlinks straight to the source directory. It is the one literal path a ticket's `CHECK:` may name. The four per-host locations `~/.codex/skills`, `~/.pi/agent/skills`, `~/.cursor/skills`, `~/.grok/skills` are retired.
_Avoid_: 通用位置, 中立目录, 用户级目录
_Home_: `docs/adr/0006-skills-install-to-neutral-dir.md`

**symlink**:
What `install.sh` makes: skills into the two install locations, assembled subagent files into each host's agent directory, `hook.py` into `~/.claude/hooks/`. A symlink is not a copy — the host reads the repository file — and whichever checkout runs `install.sh` takes over the batch. The one exception is Herdr's agent detection rule, which is copied.
_Home_: `mmw-v2/install.sh`

**stale link**:
A symlink that points back into this repository but is not on the list, or a last-generation link left in a retired location. `install.sh --check` prints `残留` and returns 1; `install.sh` removes it.
_Avoid_: 残留 (as a term; the printed prefix is a literal)
_Home_: `mmw-v2/install.sh`

**retired**:
The state of a skill or subagent moved to `deprecated/` (unchanged, not treated as fact), and of an install location that is no longer a target though its host still scans it. `install.sh` prints `退役` when it clears its own links from one.
_Avoid_: 退役 (as a term; the printed prefix is a literal)
_Home_: `AGENTS.md`

**issue tracker**:
GitHub Issues for this repository, every operation through `gh`. It is the only store of fact and state: parent–child relations, blocking links, the frontier, and claims exist only here. Its operations — Create, Read, List, Comment, Apply and remove labels, Close, Read a PR, List external PRs, Claim, Resolve — are each one `gh` command in `docs/agents/issue-tracker.md`; `publish to the issue tracker` means create a GitHub issue; `PRs as a request surface` is `no`.
_Admitted_: the tracker
_Avoid_: backlog (for this), 真 tracker, GitHub Issues (as a term)
_Home_: `docs/agents/issue-tracker.md`

**`gh`**:
The CLI every issue-tracker operation goes through. `CLICOLOR` and `CLICOLOR_FORCE` are unset before every call.
_Home_: `docs/agents/issue-tracker.md`

**Herdr**:
The terminal multiplexer that hosts every session: workspaces, panes, tabs, pane tokens, `agent_status`, and names that are unique across the whole server. The board reads it through `herdr api snapshot` and `herdr agent get`; sessions are prompted with `herdr agent prompt`. Its environment variables are `HERDR_ENV` (set when running inside Herdr), `HERDR_PANE_ID` (the caller's own pane), `HERDR_WORKSPACE_ID` (the workspace).
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**workspace**:
The Herdr unit one board answers for: it acts on the sessions whose `workspace_id` equals its own `HERDR_WORKSPACE_ID` and touches no others. `dispatch.sh run` opens the monitor tab in the workspace it is typed in, so several projects run their own nights at once. The **workspace id** (for example `w2q`) prefixes every Herdr name the pipeline hands out.
_Avoid_: 工作区 (for the git sense, that is a worktree)
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**pane**:
Where a session runs. It carries the pane tokens, the `agent_status`, `MMW_TICKET` and `MMW_AUTONOMOUS`. At `phase=closed` or `phase=handoff` the board closes only the pane — worktree and branch stay. A focused pane takes no prompt. The reviewer's pane is split from the caller's. A **tab** is what `herdr tab create` opens for a dispatched session; its label is the first `LABEL_TITLE_CHARS` characters of the ticket title.
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**monitor tab**:
The Herdr tab `dispatch.sh run` opens in the workspace it is typed in, labelled `mmw board #<spec>`, where `board.py --watch` runs. One per workspace.
_Avoid_: 监控 tab, board tab, mmw board tab
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`mmw-main`**:
The Herdr name `dispatch.sh run` gives the main agent's own pane (workspace id prefix plus `mmw-main`), so the board can re-prompt it with `mmw board:` lines. When nobody is named `mmw-main` the line waits. Its own `turn.py` hooks, installed for Claude Code, are what tell the board when it is idle enough to take one.
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**agent detection rule**:
The per-host rule Herdr classifies a session's screen with when no lifecycle authority is reporting for the pane; the dispatch skill carries an override for Cursor, and `install.sh` copies it (not links it) into `~/.config/herdr/agent-detection/`. For a session this pipeline started, `turn.py` is the authority and the rule is not consulted.
_Avoid_: Herdr agent 检测规则, agent 检测规则
_Home_: `mmw-v2/install.sh`

**worktree**:
The per-ticket git worktree `dispatch.sh` opens for the worker only, at `${MMW_WORKTREES:-$HOME/.mmw/worktrees}/<repo>/issue-<n>` on the branch `issue-<n>`, cut from the dispatching session's HEAD at the moment it opens (recorded in `branch.issue-<n>.mmw-base`) — which is why merging and dispatching are one command, `advance`. The reviewer runs inside it and the verifier is a subagent inside it. After the ticket closes the branch and the directory stay; nothing in the pipeline reclaims them. `worktree_for()` is the only source of `issue-<n>` names.
_Avoid_: 工作区, checkout (when this is meant)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**ticket branch**:
The branch `issue-<n>`. A ticket started again reuses it as it stands; `--preflight` refuses when the session is not on it; `advance` merges it into the base branch when the ticket is `CLOSED`, its closing comment's first line is `ALL MET`, the branch exists, and it is not already an ancestor.
_Admitted_: `issue-<n>`
_Avoid_: branch (bare), 分支名 (as a term)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**base commit**:
The commit recorded in `git config branch.issue-<n>.mmw-base` when the worktree was opened: the HEAD a branch was cut from, or — for a ticket branch that already existed with no record — its merge base with HEAD at that dispatch. It is the first value of the review dispatch line, where code review's diff starts (`git diff <base-commit>...HEAD`, three dots), and where the first-parent chain behind `Outside Owns:` begins. With no record, `main`. Written `<base-commit>` as a placeholder.
_Avoid_: base-commit (in prose), 起点 commit, cut point, 切点
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**base branch**:
The branch the main agent is on when it opens the night and runs `advance`: `advance` merges every ticket branch into the branch HEAD is on at that moment, so the main agent stays on the branch it opened the night on until the last `advance`. `git config branch.issue-<n>.mmw-base-branch` records it at dispatch; `advance` does not read it. The closing comment's `PR:` line reads `none — will be merged into <base branch> by dispatch.sh advance`.
_Avoid_: main branch, 基线分支, main (as a name)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**Claude Design**:
The design tool whose downloaded project is the handoff package and the baseline side of a parity run. Its page format is Design Components (`<x-dc>`, helmet, `sc-if` / `sc-for`, `data-props`, `dc-import`); its runtime is `support.js`.
_Home_: `mmw-v2/skills/claude-design-blocks/references/porting.md`

**component**:
A root-level `<name>.dc.html` page in a Claude Design project that exposes a `scene` prop, one value per state. A handoff package carries one. Its helmet pins the page root `#dc-root`, which is where the baseline side is screenshotted from. A wrapper page imports it with `<dc-import name="…" scene="…">`, whose `scene` attribute pins one scene.
_Avoid_: design component, scenario, scenario 属性, 状态开关
_Home_: `mmw-v2/skills/claude-design-blocks/references/porting.md`

**handoff package**:
A Claude Design project downloaded into the prototype leaf directory `prototypes/<task>/<issue>/UI/`: the six things the driver renders — the component's `.dc.html`, `styles/`, `data/`, `support.js`, `scenes.json`, and `vendor/` holding the three scripts `support.js` loads — plus the `README.md` a spec and its tickets take exact values, verbatim copy and `viewports` from. The screen contract's `baselines.look` names it; `visual-parity.py` and `extract_skeleton.py` render it; the Spec axis does not open it; it supersedes the winning variant under `## Read first`; once downloaded it is a contract, copied verbatim, not a reference. The target trees are its derived view.
_Avoid_: 交接包, 开发交接包, 基线目录, UI 基线
_Home_: `mmw-v2/skills/verify-ticket/references/ui-parity.md`

**scene**:
One entry of `scenes.json`: `name`, `page` (the `.dc.html` it pins), and `props` (the prop set that puts the design page into that state). The screen contract declares every scene once under `scenes`, with its page, its `reach` and its `open`, and the product is put into it through those — never through a query parameter the view answers from fixtures. Each scene gets its own screenshot, tree and class set per viewport. The name may not contain `/`, because its wrapper page is `/__parity-<name>.dc.html`. In Claude Design a scene is one value of a component's `scene` prop, switched from the Tweaks panel; the word is the same on both sides, and there is no second word for it.
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
A top-level issue that holds a batch of tickets. It is a container, not work, so it carries no label. `to-spec` writes it from the conversation, a cleared map, or an agent brief, in the `<spec-template>` shape: `## Problem Statement`, `## Solution`, `## User Stories`, `## Implementation Decisions`, `## Testing Decisions`, `## Out of Scope`, `## Sources`, `## Further Notes`. Decisions that share one seam belong in one spec. A worker reads only the subsections its ticket's `## Parent` names, plus `## Testing Decisions` and `## Out of Scope`. A section of a published spec is changed in place by `to-spec`'s step for revising a published spec — the body stays the clean current version, what changed and why goes in one comment — so the number and every ticket's `## Parent` stay valid. The night runs on it: `run <spec>`, `advance <spec>`.
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
The layer a feature's tests land in — named per layer with its directory and precedent in `## Testing Decisions` and copied into `## Seam`. The toolbox's own tests have five layers: **structural check** (`install.sh --check`, which runs `assemble.py --check`), **own-script layer** (this repository's scripts against fixed samples, entry `tests/run.sh` per skill), **vendored-script layer** (the tests that came with copied upstream scripts), **skill-behaviour layer** (run the skill for real on a throwaway ticket inside a worktree and check what appears on the ticket), and **real ticket** (one real ticket carried from writing to closing; nothing merges to the base branch until it passes).
_Avoid_: 测试层, 结构核对, 自写脚本层, vendor 脚本层, 技能行为层, 真票
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**ticket**:
A GitHub issue created as a native sub-issue of its spec (`gh issue create --parent <spec>`, or attached through the `sub_issues` API), in the `<issue-template>` shape of eight sections. It is a tracer-bullet vertical slice with its blocking links; the only place fact and state are kept; the worker's only input, read at five moments; it must have an issue number. At publication it takes one of two shapes: an agent ticket (labelled `ready-for-agent` plus a worker grade) or the separate `ready-for-human` ticket. A ticket this repository plans for itself carries a state role only. Its **ticket body** is the sections, not edited once the batch has been reported to the user as published — the read-back step, which fixes tickets and runs `--lint` again, comes before that report; its **ticket number** is `<n>` — digits only, also `{n}` in launch arguments and `$MMW_TICKET` in a `CHECK:`. A **batch** is the tickets under one spec, published together and worked in one night.
_Admitted_: issue (when naming the GitHub object)
_Avoid_: 票 (as a term), child ticket, slice (as a name), 本批, 票号, body (bare)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**vertical slice**:
The rule that a ticket cuts a narrow but complete path through every layer, by feature and never front end against back end, demoable on its own; its title and `## What to build` describe the same slice. There are UI acceptance criteria but never a UI ticket. Wide refactors are the exception.
_Admitted_: tracer-bullet
_Avoid_: 纵切, slice (as a name)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`<issue-template>`**:
The ticket template in `to-tickets/SKILL.md`: `## Parent`, `## Worker`, `## What to build`, `## Read first`, `## Seam`, `## Owns`, `## Acceptance criteria`, `## Blocked by`. Sections read by position downstream keep these exact headings; renaming one means changing `implement` too.
_Avoid_: 七节, 八节 (as names)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Parent`**:
The route from the ticket to its spec: `#<spec>, Implementation Decisions section <n>`. One of the five things a `ready-for-human` ticket holds.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Worker`**:
Which of the two worker grades the ticket goes to and one line why; `senior-worker` when getting it wrong would be wrong silently. When it is missing or names the other grade than the label, `--lint` reports `[worker-mismatch]`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## What to build`**:
The end-to-end behaviour this ticket makes work, from the user's point of view, in numbered points each with the test that decides it and the reason it is there; a choice the user settled in the `to-tickets` quiz is a point of its own. It describes the same slice as the title (checked at read-back and after claiming) and is never simplified away.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Read first`**:
The sources the ticket's spec subsections cite, `None` when there are none. Each item is read to its conclusion before work: a research file's last section, an ADR's Decision, a handoff package, a prototype's leaf README.md to its verdict. Items that record a settled conclusion are baselines. It is re-read at the Audit, and searched before a helper is written.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**baseline**:
An item under `## Read first` that records a settled conclusion: a decision ticket's resolution, an ADR's Decision, a research file's conclusion, a handoff package, a prototype's chosen artifact. To the worker it is a contract, not a reference; a handoff package is copied verbatim, a prototype is rewritten to production standard. The Spec axis reads the baselines against the diff, and a deviation is `Built wrong`. The screen contract's `baselines.look` names the handoff package directory, and `visual-parity.py`'s output word for that side is `baseline`.
_Avoid_: 基线 (as a term), reference (when this is meant)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**contract**:
The bond between a worker and every baseline in `## Read first`, in three clauses: copy exact values, wording, states, and interface shapes; never deviate quietly; never bend a baseline, a harness, or a test. **The baseline is the contract** is the first of the writing rules. **The contract does not fit** is the case where a baseline lacks a state, a field, an interaction, or a case the work needs, or two baselines conflict: keep going, open a sub-issue under the spec, add nothing quietly.
_Avoid_: 契约 (as a term), 安装契约, 接口契约, 基线是契约, 契约装不下, 基线装不下
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`## Seam`**:
Where this ticket is verified: the test layer and directory copied from `## Testing Decisions`, the precedent to copy, and how a test arrives at the state. Present and non-empty on every agent ticket; when a ticket lacks it, the worker derives it from `## Testing Decisions` and comments it on the ticket before writing code.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Owns`**:
The repository-relative paths this ticket may write, one per line — where you may write, not where the code is. It includes the Seam's test directory or file; a path the ticket creates is marked `(new)`; no absolute path, `..`, or bare `**`. Two tickets on one frontier may not overlap; where they would, a `## Blocked by` edge is added. A ticket that has a directory to itself writes a **directory glob**; several tickets dividing one directory go down to file level. The **Owns check** at start of work confirms every glob matches or is `(new)` (an older ticket derives one from its Seam). The **Owns two grades** rule handles a file outside Owns: change it and record it under `Outside Owns:` when a criterion cannot pass otherwise; leave it and open a sub-issue when the change is merely convenient.
_Avoid_: 目录 glob, Owns 核对, Owns 两档
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Acceptance criteria`**:
The ticket section holding the acceptance criteria, one after another. A `ready-for-human` ticket has none.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Blocked by`**:
Ticket numbers only, or `None (can start immediately)`: the human-readable copy of the tracker's blocking links; when the two differ, `--lint` reports `[blocked-by-mismatch]`. On a `ready-for-human` ticket it names the ticket that produces the thing.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**acceptance criterion**:
One standard on a ticket, decided by one command — a judgement that is not decided by a command is not an acceptance criterion. Four lines: `- [ ] AC<n>:`, `CHECK:`, `EXPECT:`, `EVIDENCE: pending`, with an optional `CWD:`. Three writing rules: externally observable behaviour, exact values copied from the spec or a prototype artifact, one assertion each. Numbered when the ticket is written and never renumbered, because the ledger cites by number. `--lint` checks how it is written, `verify-ticket.py <n>` runs it, the verifier re-runs it; a reviewer may not add criteria the ticket lacks.
_Admitted_: criterion
_Avoid_: AC (in prose), 标准 (as a term), 验收标准, gate (for a criterion), oracle, 判据 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`CHECK:`**:
The shell command that decides a criterion. It runs in its own shell with the working directory at the repository root (or `CWD:`); a multi-line command is written only as a fenced block directly under it. It is the one line in the pipeline a shell runs with no agent in between, so any script it names is written by its full installed path. Its text comes from the precedent named in `## Testing Decisions`.
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
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

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
One fix-and-rerun pass on one criterion. How many a criterion gets is the worker's judgement, and `--closeout` counts none: the reason on the `ABANDON:` line says what was tried. One round of code review and the board's round of re-reading are always written in full.
_Avoid_: 轮 (as a term), 三轮上限
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`ABANDON:`**:
The line `ABANDON: AC<n> <kind> <reason>` a worker — never the verifier — writes under a criterion it gives up on. The kinds: **`failed`** — it ran and did not pass (after the rounds the worker judged worth spending, or still failing after the review fix or the verifier's report), its reason saying what each round tried; **`stuck`** — it will not start or cannot be done within the ticket (a `CHECK:` that will not run, a missing credential or device, out of reach within the scope), its reason listing the routes tried or pointing at the sub-issue; neither is held to a round count, and the two are told apart for whoever reads the ticket in the morning; **`decision`** — a person has to settle one sentence, a sub-issue is opened under `needs-triage`, and it is the only kind that still lets the ticket close `ALL MET`. `failed` and `stuck` force `HANDOFF REQUIRED`.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**blocking link**:
The tracker's native dependency edge, the copy every script reads; `## Blocked by` is its human-readable copy. A **blocker** is a ticket that must close before this one starts. `--lint`'s ticket graph and the board's frontier are computed from it; GitHub's `issue_dependencies_summary.blocked_by` counts open blockers only. Adding one takes the blocker's **database id** (`gh api … --jq .id`). A blocker under another spec is reported as `cross-batch`.
_Admitted_: native issue dependencies (when naming the GitHub feature)
_Avoid_: blocking edge, dependency (for this), edge (for this), native blocking link, 上游票号, blocking ticket
_Home_: `docs/agents/issue-tracker.md`

**frontier**:
The tickets the board may start right now, in ticket order: `OPEN`, labelled `ready-for-agent`, every blocker closed, no assignee, no live session. The board announces each new set once with the `mmw board: ADVANCE` line; the main agent starts it with `advance`. `## Owns` must not overlap on one frontier. Wayfinder's frontier query (open, unblocked, unclaimed children of a map) is a different set.
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**assignee**:
The ticket field `claim` sets. It is one of `--preflight`'s six checks; a frontier ticket has none; hand back removes it.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**sub-issue**:
The tracker's native parent–child relation: every ticket is created under its spec, and `--lint`'s ticket graph, the board's frontier, and the spec page's panel all read `repos/{owner}/{repo}/issues/<spec>/sub_issues`; a spec with none is the lint `ERROR` `[no-sub-issues]`. Also an issue a worker opens under the spec with `--label needs-triage`, from one of four sources: the contract does not fit, a merely convenient change outside `## Owns`, an out-of-ticket review finding, an `ABANDON: decision`; listed on the closing comment's `Sub-issues opened:` line. A wayfinder map's child tickets are its sub-issues too.
_Admitted_: child (in the wayfinder map's context)
_Avoid_: sub_issues (in prose), child ticket
_Home_: `mmw-v2/merge-notes/to-tickets.md`

### Labels and queues

**label**:
A GitHub label on a ticket saying only which queue it is in: the five triage labels, the two worker-grade labels, and `wayfinder:*`. A spec carries none. No new label is added; `bug` and `enhancement` belong only to issues from outside. Only `--closeout` changes one; the hook refuses any other command that would.
_Avoid_: 标签 (as a term), label string (as a term)
_Home_: `docs/agents/triage-labels.md`

**queue**:
What a label expresses and nothing more. `ready-for-agent` is the **agent queue** (waiting to be dispatched or being worked; the assignee says which); `needs-triage` is the queue of what nobody has judged, the only one a skill fetches from on its own; `ready-for-human` is the user's queue, its tickets naming `reaction` or `reach`. A queue holds one shape of ticket. Only `--closeout` moves a ticket out of the agent queue.
_Avoid_: 队列, agent lane
_Home_: `docs/agents/triage-labels.md`

**triage role**:
A canonical name the skills use; `docs/agents/triage-labels.md` maps each to the label string this repository uses, which is the same string. Five **state roles** and two **category roles**; an issue from outside carries one of each, a ticket this repository plans for itself a state role only.
_Avoid_: 角色 (bare)
_Home_: `docs/agents/triage-labels.md`

**`needs-triage`**:
Nobody has judged it yet: an issue from outside, a ticket its worker closed out as `HANDOFF REQUIRED`, or a closed ticket reopened after the night because a criterion failed on the base branch (label added, assignee removed, the failing `AC<n>` and the base-branch commit in a comment). `triage` reads this queue and recommends one of the four outcomes. A sub-issue a worker opens carries it.
_Home_: `docs/agents/triage-labels.md`

**`needs-info`**:
Waiting on the user for more information; one of the four outcomes; serves only work from outside.
_Home_: `docs/agents/triage-labels.md`

**`ready-for-agent`**:
The agent queue. `to-tickets` puts it on every agent ticket beside the worker-grade label; it is one of the five frontier conditions and `--preflight`'s fourth check; without it `dispatch.sh` prints `REFUSE`; it comes off at both exits of `--closeout`; it never goes on a spec.
_Home_: `docs/agents/triage-labels.md`

**`ready-for-human`**:
One thing only a person can do, of kind `reaction` or `reach`. It is a separate ticket of a different shape holding **the five things** only — `## Parent`, which kind, What to look at (a link that opens, not a command), What makes it right, `## Blocked by` (the ticket that produces the thing) — with no Seam, Owns, criteria, or worker. Three writers (`to-tickets`, `triage`, code review's sub-issue path) and no automatic reader; the morning's second query lists it.
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
Wayfinder's single issue labelled `wayfinder:map`, the canonical index: Destination, Notes, Decisions so far, Not yet specified (the fog), Out of scope, `## Specs`. Its children are decision tickets; it is cleared when the frontier and Not yet specified are both empty, and never closed. One of the nine `## Sources` kinds.
_Admitted_: wayfinder map (in `## Sources`)
_Avoid_: shared map (in this repository's text), 地图 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**agent brief**:
The record `triage` posts on an issue at the evaluation stage — an investigation record, not a work order — ending with the disclaimer line `*This was generated by AI during triage.*`.
_Avoid_: brief (bare), 工单
_Home_: `mmw-v2/upstream/skills/engineering/triage/AGENT-BRIEF.md`

### Comments on the ticket

**ticket comment**:
One comment a script or an agent leaves on the ticket, named and keyed by its first line. A run leaves at most one; the ticket's comments are its only run state.
_Avoid_: 票评论, COMMENT (as a kind label)
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**first line**:
The first line of a ticket comment: the pipeline's protocol slot, by which `dispatch.sh wait`, `--closeout`, `advance`, `triage`, and the board recognise a comment — `NOT_READY:`, `self-run`, `reverify`, `VERDICT …`, `DECISIONS`, `REVIEW <base commit>..<HEAD commit>`, `TOUCHED BY #<n>`, `ALL MET`, `HANDOFF REQUIRED: …`, `CHECKS FAILED`, `NIGHT SUMMARY <date>`. A disclaimer therefore goes last. `NIGHT SUMMARY` lists tickets by number and first line.
_Admitted_: protocol slot
_Avoid_: 首行, 协议位, status word
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**`self-run`**:
The comment a worker's own run of `verify-ticket.py <n>` leaves: first line `self-run`, second line the gate-check summary line, then the ledger with each criterion ticked or not and its `EVIDENCE:`, ending with `Outside Owns:`. The newest `self-run` or `reverify` is where the ledger is read back from and what the board's `ac=<met>/<total>` and `--closeout` read. The run writes `phase=selfcheck`.
_Avoid_: 自跑
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**`reverify`**:
The comment the verifier's `verify-ticket.py <n> --reverify` leaves: every criterion run again, the ticked ones too; the summary line adds `reran:` and `previously met reverified:`. `--closeout` checks an `ALL MET` draft against the newest one. The run writes `phase=verify`.
_Avoid_: 复验
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**`VERDICT`**:
The verifier's judgement, posted with `gh issue comment` after its `--reverify` run: `VERDICT <full 40-character commit> by <model> — <one line>`. The one line says, in order, how it ran (`walked the flow in a running interface`, `commands only`, or `could not start`), what came back, and what it repaired. It is bound to one commit, so the branch is merged and never rebased; it covers that commit and no later one — a commit after it is listed under `Post-verdict:` and is re-run only by the base-branch `--reverify` after the night; an `ALL MET` draft needs it on the ticket, and `Post-verdict:` when HEAD has moved past it; `HANDOFF REQUIRED` is held to none of its conditions. The verifier's whole report is this line plus the two `git status --porcelain --untracked-files=no` outputs.
_Avoid_: the verdict line, verdict comment, 判决
_Home_: `mmw-v2/agents/verifier/body.md`

**`DECISIONS`**:
The comment a worker leaves on the ticket once, after the `VERDICT` and before starting the reviewer: first line `DECISIONS`, then `Decisions I made on my own` — every line so far, in the closing comment's shape — and `Outside Owns` — the `Outside Owns:` line of the newest `self-run` with one sentence per file saying why. The Spec axis reads it and judges every line; the fix round after the review adds no second one, and the closing comment carries the final version. `--closeout` does not check it.
_Avoid_: decisions comment, 临时决策评论
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**review comment**:
The reviewer's report on the ticket: first line `REVIEW <base commit>..<HEAD commit>` (the refs as given, even when one does not resolve or the diff is empty), then the three axis reports under `## Standards`, `## Spec`, `## Tests`, never merged or reordered across axes, then `## In-ticket` and `## Out-of-ticket`, then one summary line per axis. The worker waits for it with `dispatch.sh wait <n> "^REVIEW "`.
_Avoid_: review report comment, REVIEW 评论, report (bare)
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**closing comment**:
The comment a worker leaves on handing over, written first as a **draft** file that `--closeout <draft>` checks and posts. Its fixed parts: the first line `ALL MET` or `HANDOFF REQUIRED: <abandoned> abandoned (<kinds>), <unmet> unmet, <met> met of <total>`; `Branch: … Commit: … PR: none — will be merged into <base branch> by dispatch.sh advance`; `Post-verdict:` (every commit after the last `VERDICT` with where it came from, `None` when the verdict is on HEAD); four lines per criterion, with `ABANDON:` where given; `Outside Owns:` (each file followed by the Spec axis's judgement, `reasonable` or `should not`); `skipped: [X], add when [Y]` (what was deliberately not built and the condition to build it); `Sub-issues opened:`; `Counts: <met> met, <unmet> unmet, <abandoned> abandoned of <total>` (recounted at the Audit, agreeing with the first line); `Decisions I made on my own` (one line per thing the worker settled that neither ticket nor spec decides). Its first line decides whether `advance` merges the branch and whether `phase` goes to `closed` or `handoff`. The draft is written by hand, so its `ALL MET` is not evidence.
_Avoid_: 收尾评论, handoff comment, 收尾评论草稿, 草稿 (as a term), 本票我自己拿的主意
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`ALL MET`**:
The closing comment's first line when every criterion is met. `advance` merges only such tickets; `--closeout` refuses it when any `ABANDON:` is `failed` or `stuck`. Also the opening of one gate-check summary line shape, `ALL MET (<n> met…)`.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`HANDOFF REQUIRED`**:
The closing comment's other first line, `HANDOFF REQUIRED: <abandoned> abandoned (<kinds>), <unmet> unmet, <met> met of <total>` — the way out of anything the worker cannot fix itself, held to none of the `VERDICT` conditions. `--closeout` posts it, swaps `ready-for-agent` for `needs-triage`, and leaves the ticket open. gate-check's summary line has a same-prefixed shape, `HANDOFF REQUIRED: <n> abandoned (met: …)`.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`CHECKS FAILED`**:
The comment `--closeout` posts instead of the draft when `.mmw/target.json`'s `checks` had a non-zero exit: first line `CHECKS FAILED`, then each failed command and its last 20 lines of output. The ticket stays open, still assigned, still `ready-for-agent`.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`CHECKS OK`**:
The line `--closeout` appends to an `ALL MET` closing comment when every `checks` command exited 0: `CHECKS OK <n>/<n>`. Absent when the key is absent.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`Outside Owns:`**:
The last line of a `self-run` or `reverify` comment and a fixed line of the closing comment: the files this ticket's own commits changed that no `## Owns` glob covers, along the first-parent chain since the base commit, merges excluded; computed by `verify-ticket.py`, copied into the draft, explained there with the Spec axis's judgement of each file (`reasonable` or `should not`); `None` when empty. The `DECISIONS` comment carries the same line with one sentence per file, the Spec axis judges each, and before the draft is written the worker leaves a comment opening `TOUCHED BY #<n>` on every open ticket under the same spec whose `## Owns` covers that file, saying what changed, why, and the judgement. No script finds those tickets and `--closeout` checks none of this. The question is asked of this ticket's own commits, so a run on any branch but `issue-<n>` writes `Outside Owns: not checked on <branch>, which carries more than this ticket` instead. It is an explanation, not a criterion.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**`NOT_READY:`**:
`NOT_READY: <reason>`, what `--preflight` posts on the ticket and prints when it refuses; exit 2; the worker stops.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**question gate**:
`hook.py question <host>`: the refusal of the host's question tool (`AskUserQuestion` on Claude Code, `ask_user_question` on Grok, `request_user_input` on Codex) in any session carrying `MMW_AUTONOMOUS=1`. Its reason names the two ways out — take the likeliest option and record it under `Decisions I made on my own`, or `ABANDON: AC<n> decision` with a sub-issue — so no question ever reaches a screen nobody watches.
_Avoid_: form, 提问表单, BLOCKED:
_Home_: `mmw-v2/skills/verify-ticket/scripts/hook.py`

**`NIGHT SUMMARY`**:
The comment `NIGHT SUMMARY <date>` the board posts on the spec when nothing is left to run: four lines, `Closed:`, `Handed back to needs-triage:`, `Not dispatched, a blocker stayed open:`, `Sub-issues opened tonight:`, ticket numbers and first lines only.
_Avoid_: 夜间总结, the night summary
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

### Running the criteria

**ledger**:
The temporary file `AC.md` that `verify-ticket.py` writes from `## Acceptance criteria` and `## Owns` — or from the newest `self-run` or `reverify` comment — and hands to gate-check, the only format gate-check accepts. It cites criteria by `AC<n>` number, carries an `OWNS:` line, and is deleted after use; the updated ledger is posted back as the `self-run` comment.
_Avoid_: 账本, 临时账本, AC.md (as a name), throwaway ledger
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**gate-check**:
The judging program copied from unlazy: it walks the ledger, runs each `CHECK:` one at a time in its own shell, applies both conditions, writes `EVIDENCE:`, prints one **status line** per criterion (`RUN`, `PASS`, `FAIL`) and one **gate-check summary line** at the end — `ALL MET (<n> met…)`, `UNMET: <n> (met: <m>)`, or `HANDOFF REQUIRED: <n> abandoned (met: …)` — which is copied into the second line of every `self-run` and `reverify` comment. `gate-check.mjs` names the file. Its `--claim`, `--release`, `--scope` and `GATES.md` are unlazy features this pipeline does not use.
_Avoid_: the judging engine, gate checker, the checker (for this), 汇总行
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`

**gate-lint**:
The criterion linter copied from unlazy: it reports problems in how criteria are written and runs no command; `manual-gate` is an error here. It prints `LINT OK` or `LINT FINDINGS`. `--lint` runs it.
_Avoid_: the linter (for this)
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-lint.mjs`

**lint**:
`verify-ticket.py <n> --lint`: gate-lint, plus the ticket graph (`cycle`, dangling references, `cross-batch`, `blocked-by-mismatch`), plus the worker-label check. Every finding carries a problem tag and a level, `ERROR` or `WARN`; only `ERROR` affects the exit code. When the graph has no cycle and no dangling reference it prints the **start levels** — the order tickets may be started in, built from this spec's own blocking links. A batch converges when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose. It is run at the read-back step.
_Avoid_: 票图核对, the linter (for this), 启动层级
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**problem tag**:
The label a lint finding carries: from gate-lint `parse`, `tautological-check`, `weak-expect`, `path-read-as-regex`, `manual-gate`, `unmeasured-number`, `activity-not-outcome`, `mostly-manual`; from `verify-ticket.py` `dollar-without-m` (`ERROR`), `shared-state`, `unexplained-edge`, `cross-batch`, `cycle`, `duplicate-ticket`, `blocker-not-a-ticket`, `blocked-by-mismatch`, `no-sub-issues`, `worker-label` (`ERROR`: no worker-grade label, or both), `worker-mismatch` (`WARN`: `## Worker` missing or naming the other grade).
_Avoid_: 问题标签
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`ERROR`, `WARN`**:
The two lint levels. gate-lint prints `ERROR` and `WARN `; `--lint`'s exit code says only whether an `ERROR` is left.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

### Code review

**code review**:
One round: the worker starts the reviewer session through the dispatch skill; the dispatcher starts three read-only axis subagents, each given three values — the base commit, the ticket number, and its reference file's path — each reading `git diff <base-commit>...HEAD`; one review comment results. The worker waits with `dispatch.sh wait <n> "^REVIEW "` (the script's own timeout) and the round ends only with the review comment: on a start that exits 1 or 2 or a wait that times out, the worker reads the reviewer's screen, waits again while it is running, and otherwise runs the `code-review` skill in its host's general-purpose subagent, whose report lands with the same `REVIEW` first line. An in-ticket finding gets one round of fixes and a self-run, never a re-review; an out-of-ticket finding becomes a sub-issue. Fixing a finding is bound by the writing rules.
_Avoid_: the review stage
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**axis**:
One of the three dimensions of a code review, each a read-only subagent with its own reference file whose H1 is the subagent's name. **Standards axis** (`Standards reviewer`): does the change follow this repository's documented coding standards, and does the same outcome exist with less code — from the documented standards, the **smell baseline** (the twelve Fowler smells, carried in full inside the reference file and never pasted into a prompt), and `codebase-design/SKILL.md`; it asks of every hunk whether it could be less, and marks a finding `judgement call` or `hard violation`. **Spec axis** (`Spec reviewer`): does the change match what the ticket or the spec asked for, reading the baselines under `## Read first` and never the handoff package; findings are `Missing`, `Scope creep`, or `Built wrong`; it also judges every line of the ticket's `DECISIONS` comment `reasonable` or `should not`, and a `should not` is an in-ticket finding. **Tests axis** (`Tests reviewer`): are the test cases the criteria name worth trusting — its in-ticket scope is the test files and cases a `CHECK:` names, any other test file in the diff is out-of-ticket, from the **test smell baseline** copied from `tdd/tests.md` and `tdd/mocking.md`; it reports no coverage and adds no criteria the ticket lacks.
_Avoid_: 轴 (for this), Standards 轴, Spec 轴, Tests 轴, 缺项, 实现得不对, baseline smell, smell list
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**review finding**:
One item an axis subagent reports, quoting the requirement line it fails. It is **in-ticket** when it touches this ticket's acceptance criteria, a decision in the spec section the ticket names, a baseline under `## Read first`, the spec's `## Out of Scope`, or the spec's `## Testing Decisions` — then it gets one round of fixes, and `ABANDON: AC<n> failed` if the fix cannot be made; otherwise it is **out-of-ticket** and becomes a non-blocking sub-issue under `needs-triage` while the ticket still closes. The dispatcher sorts them.
_Avoid_: finding (bare), 票内, 票外, 票内发现, 票外发现
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

**reference file**:
A document under a skill's `references/` directory, reached by a relative link from its `SKILL.md`. For code review it is one per axis and the subagent's only instructions, handed over as the absolute path `~/.agents/skills/code-review/references/<axis>.md`.
_Avoid_: reference (bare), 判据 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/code-review/SKILL.md`

### UI acceptance

**`visual-parity.py`**:
`scripts/visual-parity.py` beside the verify-ticket `SKILL.md`: it decides whether an interface matches the design it was built from (**interface parity**). Given `--contract` and `--mount <id,id>` (and `--scenes` to narrow), it takes the scenes under those mounts, puts the product into each through the driver (`reach`, `route`, `open`), measures the mount element's box, renders the design page offline pinned to that box, and compares the three judges at every contract viewport: the tree after normalisation, the class set, and pixels over the box's intersection with the viewport (`--max-pct`, the pixel share after both screenshots are shrunk by 4, default 3%). Its output word for the design side is `baseline`. It prints `PARITY OK <passed>/<total> pixel<=<worst>%` (exit 0), or one `DIFF <scene> <viewport> <pct>% box=… — <reasons>` line per failing scene and viewport (exit 1, with `baseline` / `impl` / `only in baseline` / `only in impl` sub-lines for tree differences, `class only in …` lines for class differences, and `around: <elements>` on a pixel failure), or `NEGATIVE CONTROL FAILED` (exit 2, no parity conclusion; also exit 2 when the product is not ready). `--out <dir>` keeps the screenshots, trees, and differing-pixel pictures for the user to look at; `--render-only` renders the design side alone; `--shows-perturbation` is the perturbation run. No address is on its line. It is the one script a ticket's `CHECK:` names by full installed path, `uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py …`, because a shell runs it with no agent between. One execution is a **parity run**.
_Avoid_: visual parity, UI parity, 视觉对等, UI acceptance (when the script is meant)
_Home_: `mmw-v2/skills/verify-ticket/references/ui-parity.md`

**negative control**:
The pair each judge builds to prove it can fail, judged before any real result. Interface parity's: after the first scene at the first viewport, the baseline server serves that scene's own address with an error banner in the served bytes, the product is captured again, and the two must differ — equal means the product capture read the design's server, and the run stops with `NEGATIVE CONTROL FAILED`. The wiring check's: `--negative` breaks the state transport and requires every row to `MISS` on an `observe` assertion, printing `WIRING NEGATIVE OK <n>/<n>` or `GREEN WITHOUT TRANSPORT <row>`.
_Avoid_: 负控制
_Home_: `mmw-v2/skills/verify-ticket/scripts/visual-parity.py`

**normalisation**:
How an accessibility tree is read before comparison: as the sequence of its named nodes in reading order — role, name or text, and state attributes — each followed by ` < ` and its nearest named ancestor, with unnamed wrappers and landmark names dropped. One normaliser, in `screen_driver.py`, serves interface parity, the wiring check's tree observe, and the target trees. The **accessibility tree** and the **class set** are read over the whole subtree under the mount; the pixel judge sees only the mount's box intersected with the viewport, on both sides.
_Avoid_: 归一化, ARIA 归一化, ARIA 树, 视口
_Home_: `mmw-v2/skills/verify-ticket/references/ui-parity.md`

### Screen contract

**screen contract**:
`docs/specs/<effort>/screen-contract.yaml`, two axes. The **control axis**, `rows`: one row per user-visible behaviour of an interface — the control (`trigger`, by role and accessible name), its `precondition`, the `scenes` it is visible in, what it `calls`, which field feeds each value it `shows`, what state is `next`, what `on_failure` shows, where the behaviour was decided (`source`), how a test reaches the state (`reach`), and whether design and backend agree (`gap`). The **screen axis**: `target` (`kind`, `adapter`), `viewports`, `pages` (one per design page: `mount`, `route`, and a `Component · ` page's `component`) and `scenes` (one per scene: `page`, `reach`, `open`, overrides), plus the mechanism table with `via` and `built_by`. It carries no address. Written by `align-screens` on the alignment ticket; read by `to-spec`, `to-tickets`, `implement`, the Spec axis, both judges and `verify-ticket --lint`. It is the behaviour baseline of an interface, beside the handoff package as its look-and-copy baseline; the two never bind the same thing.
_Avoid_: UI contract, interaction table, 界面合同表, 对齐表
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

**alignment ticket**:
The last ticket of a wayfinder map whose destination has an interface: a `grilling` ticket, blocked by every decision ticket and by the ticket that produces the handoff package, resolved by running `align-screens` and closed when every row's `gap` is `aligned`.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**gap list**:
The rows of a screen contract whose `gap` is `design-only` or `backend-only`, plus every `reach` with no mechanism, written by `align-screens` for the person to settle — the one judgement in that skill that is theirs.
_Avoid_: 差集
_Home_: `mmw-v2/skills/align-screens/SKILL.md`

**mechanism registry**:
What `## Testing Decisions`'s **How a test arrives at a state** becomes when the spec has a screen contract: named entries of three kinds — `seed:<state>` (the product put into a state through its own write surface, `via: api`; `via: storage` is the declared exception and names its `proven_by` criterion; values and counts from `data/fixtures.js`), `stub:<seam>-<script>` (an external seam answering by script), `dev:<capability>` (a registered dev-only capability outside the view layer) — each with the ticket that builds it (`built_by`), referenced by the contract's `reach` column and its `scenes`, and run through the repository's reach script named in `.mmw/target.json`.
_Avoid_: reach registry, 机制登记表
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**contract ticket**:
The first ticket cut from a spec with a screen contract: the empty shell behind every declared `route`, each landing on an element carrying its `data-screen` mount; `ready`; the reach script with every mechanism; one passing minimal test per test layer (the precedent for the tickets behind it); `.mmw/target.json`; the single-code-path guard; and what the target's reference file adds (on electron the models, `501` route signatures, OpenAPI export and generated client types). It carries the **addressing self-check**: for every scene, `reach`, fill the route, navigate, assert `data-screen="<mount>"` — the whole addressing model against an empty surface. Every other ticket of the batch is blocked by it.
_Avoid_: 合同票, prefactor ticket (for this one)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**wiring criterion**:
An acceptance criterion in the fixed shape of `references/wiring-check.md`, running `scripts/wiring-check.py --contract … --rows …`: for each row, put the product into its `reach` state through the reach script, open its `route` through the target's adapter, trigger the control, read its `observe` lines through the target's read surface. Prints `WIRING OK <passed>/<total>` or `MISS <row id> — <reason>`; with `--negative`, `WIRING NEGATIVE OK <n>/<n>`. No address is on its line. A criterion that stubs the application's own network is not one.
_Admitted_: wiring check (for the run)
_Avoid_: 接线测试, integration criterion
_Home_: `mmw-v2/skills/verify-ticket/references/wiring-check.md`

**`screen_driver.py`**:
`scripts/screen_driver.py` beside the verify-ticket `SKILL.md`: the one driver both judges and `extract_skeleton.py` import — the contract's screen axis, `.mmw/target.json`, the adapters, the baseline server and its CDN answering (`vendor/`, cache, network), the controlled clock, `capture`, the normaliser and the class set. Nothing in it judges.
_Avoid_: the driver module, 共用驱动
_Home_: `mmw-v2/skills/verify-ticket/scripts/screen_driver.py`

**target**:
What kind of product the judges drive, named in the contract as `target.kind` — `electron`, `web-spa`, `web-server-rendered`, `chrome-extension` — with `target.adapter` pointing at the kind's reference file under `verify-ticket/references/targets/`. The **adapter** is the class in `screen_driver.py` that answers the kind's **platform capabilities**: `attach`, `ready`, `address`, `release`, `transport` (the write half) and `observe` (the read half), plus how to break the transport. `targets/README.md` is the extension point: the seven questions a new kind answers.
_Avoid_: platform (bare), 目标 (as a term), 适配器
_Home_: `mmw-v2/skills/verify-ticket/references/targets/README.md`

**`.mmw/target.json`**:
The consuming repository's machine facts, read by the driver and never written in a contract or a criterion: `start` (a command that brings the product up, choosing inside itself everything the product needs, and returns once it answers — the driver runs it when `ready` finds nothing answering, so no agent starts the product by hand), `discover` (a command printing one JSON object of addresses), `reach` (the reach script the mechanism names are appended to), `transport_off` and `transport_on`, and optional `checks` (shell commands `--closeout` runs at the repository root after an `ALL MET` draft is accepted and before the ticket closes — the consuming repository's rule that the worker run the tests themselves, made a gate). Addresses change per machine and per worktree; this file is where they are answered afresh.
_Avoid_: target config, 地址文件
_Home_: `mmw-v2/skills/verify-ticket/references/targets/README.md`

**`checks`**:
The optional key of `.mmw/target.json`: a list run in order at the repository root by `--closeout` only, after the draft is accepted and before an `ALL MET` ticket closes. An entry is a command string, held to `DEFAULT_TIMEOUT`, or `{"run": …, "timeout": …}` held to its own bound. Any non-zero exit posts `CHECKS FAILED` and does not close; every command exiting 0 appends `CHECKS OK <n>/<n>` to the closing comment. A `checks` value that is not a list, an entry of another shape, or a file that is not JSON, is `CHECKS FAILED`, not absence. `--reverify`, `--lint`, `--check-only`, and a `HANDOFF REQUIRED` draft do not run them. A repository without the key is unchanged.
_Home_: `mmw-v2/skills/verify-ticket/references/targets/README.md`

**reach script**:
The consuming repository's own script that `transport` runs with mechanism names appended (`seed:library-ready dev:image-select-path`, and `--perturb` for the perturbation run), idempotent, printing `KEY=VALUE` lines that fill `{placeholders}` in routes, `open` values and `observe` paths, and `cookie=` for a web target's session.
_Avoid_: seed command, `--seed`
_Home_: `mmw-v2/skills/verify-ticket/references/targets/README.md`

**mount**:
A design page's `mount` in the contract's `pages`: the value of the `data-screen` attribute on the one product element that page *is*. Its subtree is what the tree and the class set read; its box, measured after the viewport override, is what the pixel judge compares and what the design's `#dc-root` is pinned to (`frame_box`). Declared by the person writing the contract, never derived from rows; unique in one render; a scene may override it to the page root's id for a top-level dialog. Scenes belong to tickets by mount, and a parity criterion names the ticket's mounts with `--mount`.
_Avoid_: mount point (for this), 挂载点, data-screen-label, test hook (for this)
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

**two-level model**:
`App · ` scenes compare the whole surface — which components are on it and what box each gets; `Component · ` scenes compare the block the product gives that one component. It rests on the page-kind prefix the `claude-design-blocks` skill enforces, not on the product; a package of whole pages makes every scene whole-surface.
_Avoid_: 两级模型
_Home_: `mmw-v2/skills/verify-ticket/references/ui-parity.md`

**target trees**:
`docs/specs/<effort>/targets/<page>.aria` and `<page>.classes`, one pair per design page, written by `extract_skeleton.py --targets` with the judges' own normaliser: every scene's normalised tree and class set, headed by the sha256 of `scenes.json` and of the page. The handoff package's behavioural counterpart and a derived view of it — the package is the baseline, the tree the view, the hashes what keeps them from disagreeing (the contract lint fails when they do). An interface ticket lists its pages' pair under `## Read first`, found from its row ids through `component` to the page; the worker writes toward them.
_Avoid_: 目标树, target elements, expected tree
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

**class set**:
The third judge of interface parity: the set of class names in the subtree under the mount, runtime prefixes (`sc-`, `dc-`) removed, compared as a set; a class one side lacks fails the scene and names the first element wearing it. Its reason to exist: the stylesheets are copied byte for byte, so a wrong colour or gap on the right element is a wrong class, which the tree cannot see and a pixel share cannot name.
_Avoid_: 类名集合, class list
_Home_: `mmw-v2/skills/verify-ticket/references/ui-parity.md`

**`volatile_values`**:
A top-level list on the screen contract of display values the seed must not write — a wallet balance belonging to an external account, not a difference to hide. Each entry is a `page`, a `trigger` (role and accessible name, the same shape as `retired_ids`), and one line of `reason`. Before the accessibility tree and the pixel judge compare, both sides replace that node's text with one token: the tree name becomes `<volatile>`, and the pixel judge puts the trigger's digits into the node on both sides, so the boxes are one width, and paints that box the same solid colour. The class set is not masked — the paint is an inline style, not a class name. A product node matches when its role equals the trigger's and the accessible names agree once digits and thousands separators are removed. The lint prints every entry on every run and warns when the trigger is not in that page's target tree.
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

**perturbation run**:
`visual-parity.py --shows-perturbation`: every scene seeded twice, from `data/fixtures.js` and then with other values (`--perturb` to the reach script), and every scene whose rows declare `shows` must read differently — `SHOWS OK <n>/<n>`, or `SHOWS-STATIC <scene>` for a value that is hard coded or fed from the wrong field.
_Avoid_: 扰动运行
_Home_: `mmw-v2/skills/verify-ticket/references/ui-parity.md`

**addressing self-check**:
The contract ticket's criterion that needs no interface: for every scene declaration, run `reach`, fill the `route`, navigate, and assert an element with `data-screen="<mount>"` — the whole addressing model proved against an empty surface, and nothing about look or copy.
_Avoid_: 寻址自检
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

### Dispatch and the night

**landing pipeline**:
The whole path from spec to closed ticket: four steps by day (vocabulary, spec, tickets, lint), eight by night (a worker session from start of work to closing), two in the morning (the user takes over). Its only place to close a ticket or change a label is `--closeout`; its protocol slot is a comment's first line; it pushes no branch and reads no pull request; it reclaims no branch or worktree; it does not chase test coverage.
_Admitted_: ticket pipeline (in triage text)
_Avoid_: 流水线, this pipeline (as a name), 落地流水线
_Home_: `docs/research/code-landing/11-target-pipeline.html`

**publish**:
Creating the spec or the tickets as GitHub issues (`publish to the issue tracker`): each ticket as a native sub-issue of its spec, labelled `ready-for-agent` plus a worker grade, or `ready-for-human`. The **read-back** step follows: every ticket is read back — title and `## What to build` describe one slice, `## Blocked by` resolves, the native edge count matches, the spec's sub-issue count equals the batch, `## Read first` and `## Seam` are non-empty — and every ticket with criteria is run through `--lint`.
_Avoid_: 发布 (as a term), 出票 (as a term), 回读 (as a term)
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**dispatch**:
Turning a ticket into a live session that carries its ticket number, worktree, and Herdr name: `dispatch.sh <ticket> worker|reviewer [base-commit]`. The script checks the ticket may start, reads the role's row of `models.md`, opens the worktree and records the base commit, opens a tab and starts the session through Herdr, waits for idle, and sends the dispatch line. The caller gives only the ticket number and `worker` or `reviewer`; there is no parallelism budget. A ticket or session that has been through it is **dispatched**.
_Avoid_: 派发 (as a term)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`dispatch.sh`**:
The dispatch skill's script, four forms: `<ticket> worker|reviewer [base-commit]`, `wait <ticket> "<first-line-regex>" [seconds]`, `advance <spec>`, `run <spec> [--max-hours H]`. It writes the pane tokens `ticket`, `kind`, `model`; injects `MMW_TICKET` and `MMW_AUTONOMOUS`; records `branch.issue-<n>.mmw-base`; reads the worker-grade label and nothing else to pick the row. Exit codes: 2 when the ticket fails its checks (`REFUSE …` on stderr), 1 when the session was not reported ready within 120 seconds or did not report the prompt taken, 3 when `advance` hits a conflict. The skill's own text calls it `<dispatch>`.
_Home_: `mmw-v2/skills/dispatch/SKILL.md`

**dispatch line**:
The two sentences a session is given when dispatched — which skill to use, on which ticket, and that nobody is watching: `Use the implement skill to work ticket #<n>.` for a worker, `Use the code-review skill to review ticket #<n> from base commit <base-commit>.` for a reviewer, each followed by `You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work.` Any wording that carries the two values and that sentence is a correct call. A session already running gets `continue` instead.
_Avoid_: 派发 (as a term)词, prompt (bare)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`MMW_TICKET`**:
The ticket number `dispatch.sh` injects into the worker's tab environment: the hook's only source for which ticket the session guards — no variable, no gate. A reviewer, the main agent, and an ordinary session have none. A `CHECK:` may read `$MMW_TICKET` for the ticket number.
_Home_: `mmw-v2/skills/verify-ticket/scripts/hook.py`

**`MMW_AUTONOMOUS`**:
The variable `dispatch.sh` sets to `1` on the worker's tab and the reviewer's pane: the mark of a session nobody watches, and the question gate's only source for whether to refuse. The main agent and an ordinary session have none.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**pane token**:
A named value on a Herdr pane, written with `herdr pane report-metadata <pane> --source mmw --token k=v --ttl-ms TOKEN_TTL_MS` (one day): `ticket`, `kind` (`worker` or `reviewer`), `model` by `dispatch.sh` at dispatch; `phase` and `ac=<met>/<total>` by `verify-ticket.py` (which can also `--clear-token`); `turn` and `turn_id` by `turn.py` on the host's lifecycle hooks. The board reads them through `herdr api snapshot`; nothing on screen is consulted.
_Avoid_: Herdr pane token, token (bare)
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`phase`**:
The pane token saying where a worker is, written only by `verify-ticket.py`: `selfcheck` (a run that is not a reverify), `verify` (`--reverify`), `implement` (after a successful claim), `closed` and `handoff` (the two `--closeout` exits), `closeout-rejected`. The board reads it together with `agent_status`.
_Avoid_: stage (for this)
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`agent_status`**:
Herdr's lifecycle state of a session, one of `working`, `idle`, `done`, `blocked`, `unknown` (the board's default when Herdr reports none). For a session this pipeline started it is what `turn.py` reported through `herdr pane report-agent`, which makes that script the pane's lifecycle authority and stops Herdr reading the state off the screen; `idle` and `done` are the settled states. Without a reporting authority Herdr classifies the screen with its agent detection rule, a guess the board acts on only through `FALLBACK_SECONDS`.
_Avoid_: status (bare)
_Home_: `mmw-v2/skills/dispatch/scripts/turn.py`

**`turn`**:
The pane token saying how a session's newest turn stands, written by `turn.py`: `ready` (`SessionStart`), `working` (`UserPromptSubmit`), `ended` (`Stop`), `failed:<error>` (`StopFailure`, `<error>` the host's error class), `cancelled:<reason>` (`StopCancelled`). `turn_id` beside it is the turn's `promptId`, so a late report for an older turn is dropped. The board reads `turn` and nothing else to choose between `continue` and `STOPPED`.
_Home_: `mmw-v2/skills/dispatch/scripts/turn.py`

**`turn.py`**:
`scripts/turn.py` of the dispatch skill, `turn.py <host>`: registered by `install.sh` on each session host's lifecycle hooks (`SessionStart`, `UserPromptSubmit`, `Stop`, `StopFailure`, `StopCancelled`, `Notification` `idle_prompt`, `SessionEnd`, as far as the host fires them). On each it reports `working` or `idle` to Herdr under the source `mmw:<host>` and writes the `turn` token; on `SessionEnd` it releases the authority. It does nothing outside Herdr and nothing for a subagent's events. Grok fires `SessionStart` with the first prompt rather than at process start, so a `SessionStart` arriving over a `turn` already on the pane is dropped.
_Home_: `mmw-v2/skills/dispatch/scripts/turn.py`

**`pane event`**:
A Herdr `pane.updated` or `pane.closed` push the board acts on; between pushes it re-reads everything every `SNAPSHOT_INTERVAL`.
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**preflight**:
`verify-ticket.py <n> --preflight`, the worker's first step: six checks — on the ticket branch, no uncommitted tracked changes, ticket state `OPEN`, labelled `ready-for-agent`, no open blocker, no assignee — then the claim and `phase=implement`, printing `READY: #<n> claimed on issue-<n>`. Any failure posts and prints `NOT_READY: <reason>` and exits 2. The checks are all in the script; the model does not perform them one by one.
_Admitted_: start-of-work guard
_Avoid_: 开工守卫, 开工核对, the guard (for this)
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**claim**:
Setting the ticket's assignee to oneself, `gh issue edit <n> --add-assignee @me`: the first write action after preflight's checks pass, and the session's first write. A claim exists only on the tracker.
_Avoid_: 认领 (as a term), assign to oneself
_Home_: `docs/agents/issue-tracker.md`

**wait**:
`dispatch.sh wait <ticket> "<first-line-regex>" [seconds]`: blocks until the first line of a comment matches — the newest one when the wait starts, then any comment added since, so a comment landing after the awaited one does not hide it; on timeout it comments on the ticket first, then exits non-zero; whoever waited on a worker skips that round, and a worker that waited on its reviewer reads the reviewer's screen and waits again or reviews in its own subagent. It takes only a ticket number. A worker waits for its reviewer with `"^REVIEW "`; whoever dispatched a worker waits with `"^(ALL MET|HANDOFF REQUIRED)"`. The default is `WAIT_DEFAULT_SECONDS` in the script, not in skill text.
_Home_: `mmw-v2/skills/dispatch/SKILL.md`

**run**:
`dispatch.sh run <spec> [--max-hours H]`, the one command that opens a night: it runs `install.sh --check` and refuses on any missing item, reads every queued ticket's worker-grade label through `board.py --worker-grades` and refuses when one names a row `models.md` lacks or a ticket carries two, refuses when a worker row's or the reviewer row's host is not a kind `herdr agent start` accepts, then renames the main agent's pane `mmw-main`, opens the monitor tab in this workspace, and starts `board.py --watch`. Every refusal is exit 2 with nothing opened. It dispatches nothing.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**advance**:
`dispatch.sh advance <spec>`: first merge the branches of the tickets that closed, by closing time from earliest to latest, into the base branch — a ticket is merged when it is `CLOSED`, its closing comment's first line is `ALL MET`, its branch exists, and it is not already an ancestor; one merge commit each; `MERGE_TRIES` retries against a worker's commit in its own worktree holding the shared `.git` lock, and exit 2 when every try fails — then dispatch the frontier as `board.py --advance-plan` lists it (`MERGE <n>` and `DISPATCH <n>` lines, the **advance plan**). A conflict is left in place with exit 3 and a **conflict report** on stderr (`CONFLICT` and `MERGE_HEAD` lines naming the two tickets and files); the main agent resolves it with `resolving-merge-conflicts` — never `--abort` — runs this repository's checks, commits the merge, and runs `advance` again. Uncommitted changes in the working tree give exit 2. It ends with the **advance summary line** `advance #<spec>: merged <m>, already in <s>, started <n>, refused <r>`, and may be run repeatedly. It is the main agent's answer to `mmw board: ADVANCE` and `night over`.
_Avoid_: 并回来 (as a term)
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**night**:
Everything between the last ticket published and the morning: `run` opens it, `board.py --watch` reads the sessions, `NIGHT SUMMARY` ends it. Two agents share it — the board watches and reports, the main agent decides — and one workspace holds one night. A ticket leaves the night in one of two ways: by its worker's closing comment, or by staying in the agent queue behind an open blocker all night, which the `Not dispatched, a blocker stayed open:` line of `NIGHT SUMMARY` lists. The night ends when the frontier is empty and no dispatched session is alive. **`night over`** is the `mmw board:` case saying the summary is the spec's newest comment: run `advance` one last time.
_Avoid_: 夜间编排主循环, night orchestration loop, 夜里 (as a term), 夜间 (as a term)
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**morning**:
The user takes over with the two **morning queries**, `is:open label:needs-triage` (which `triage` reads) and `is:open label:ready-for-human` (which the user reads); the commands are in `docs/agents/issue-tracker.md`.
_Avoid_: 早上 (as a term), 早上两条查询, the two morning queries
_Home_: `docs/agents/issue-tracker.md`

**wakeup loop**:
The rule table `board.py --watch` applies after every pane event or every `SNAPSHOT_INTERVAL`, for each worker session in its workspace, read off the `turn` token: `failed:<error>` with `phase` not `closed` or `handoff` — send `continue`, once per turn and at most `FAILED_LIMIT` times at one phase, then `STOPPED` instead; `ended` or `cancelled:<reason>` with `phase` not `closed` or `handoff` — queue `STOPPED` for `mmw-main`, once per turn; `closed` or `handoff` — close the pane; `working` or `ready` — nothing; no token — nothing until `agent_status` has been `idle` or `done` for `FALLBACK_SECONDS` with the ticket's comments and `phase` unchanged, then `STOPPED`. A reviewer is never touched. Nothing in the table changes a label or starts a session.
_Avoid_: 唤醒闭环, the board's state machine
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**re-prompt**:
Sending a settled session a new prompt with `herdr agent prompt`. The board does it in one case, a worker whose turn failed, and sends `continue`; the main agent does it after reading a `STOPPED` or `TIME LIMIT` session's screen, with what it settled and `continue`; the main agent itself gets one `mmw board:` line. Only while the target's pane is not focused and it is not `working`.
_Avoid_: 重新 prompt, wake up, wakeup (as a verb), 唤醒, 扶起来
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**`continue`**:
The whole of the board's re-prompt to a worker (`CONTINUE_LINE`): the session is alive and holds everything it read and wrote, so it resumes at the closing step after the newest of `self-run`, `VERDICT`, `DECISIONS`, `REVIEW`.
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**hand back**:
Swapping `ready-for-agent` for `needs-triage` and leaving the ticket open: `--closeout` does it on `HANDOFF REQUIRED` (printing `HANDED BACK: #<n> is now needs-triage and stays open`), and nothing else in the pipeline does. `triage` reads such a ticket from its comment trail instead of reproducing it.
_Avoid_: 交回, handed back (as a name)
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`STOPPED`**:
The `mmw board:` case for a worker that ended a turn on its own short of `closed` or `handoff`, failed more than `FAILED_LIMIT` turns at one phase, or sat `idle` for `FALLBACK_SECONDS` with no `turn` token: `mmw board: STOPPED #<n> at phase=<phase> — read <name> with herdr, then move it on with the dispatch skill`. The main agent reads that session's screen with `herdr agent read`, settles what stopped it, and re-prompts it; the ticket keeps its label.
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**`TIME LIMIT`**:
The `mmw board:` case for a ticket that has held its session for `MAX_HOURS` (`--max-hours`): `mmw board: TIME LIMIT #<n> — <hours> h at phase=<phase>; read <name> with herdr and decide with the dispatch skill`, sent once. Nothing else changes: label, pane and session stay.
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**`mmw board:` line**:
The one line the board sends `mmw-main`: `mmw board: <case> #<n> — <what to do> with the dispatch skill`, `<case>` one of `ADVANCE`, `night over`, `STOPPED`, `TIME LIMIT`. The main agent answers the first two with `advance` and the other two by reading that session's screen.
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**board log**:
`~/.mmw/logs/board-<workspace id>-<spec>.log`, where `board.py --watch` appends every line it prints, dated; the record of the night once the monitor tab is closed.
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**triage**:
The skill that moves an issue from outside through the state machine of triage roles: it reads the `needs-triage` queue, recommends one of the four outcomes (`needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix` — staying at `needs-triage` is not one), posts an agent brief at the evaluation stage, and ends every comment with the disclaimer. An issue judged to be agent work enters the landing pipeline through `to-spec` and then `to-tickets`; tickets `to-tickets` wrote are not triaged.
_Avoid_: 人拍板
_Home_: `mmw-v2/upstream/skills/engineering/triage/SKILL.md`

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
The While writing code section of `implement`, between stating the seam and `Use /tdd`: the baseline is the contract (open a sub-issue when it does not fit); `Put no question on the screen` — take the default and record it under `Decisions I made on my own`; before changing a function, grep every caller and fix the shared place; before adding a branch or guard, name and delete the one it makes redundant; before writing a helper, look for one in the repository and `## Read first`; before adding a file, dependency, or configuration, say why the existing one is not enough; never simplify away security, data-loss prevention, accessibility, or what the ticket explicitly asks for (`## What to build`, every criterion, the baselines, the Seam interface); Owns two grades.
_Admitted_: While writing code
_Avoid_: 写码纪律, 写码纪律七条, the seven working rules, 不问 (as a name)
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**closing steps**:
What `implement` does once the code is written: self-run (as many rounds per criterion as the worker judges worth spending); dispatch the verifier with `verify #<n>`, once; comment `DECISIONS` once; start the reviewer and wait for the review comment, fix in-ticket findings for one round, no re-review; `Audit`; comment `TOUCHED BY #<n>` on every open ticket of the spec whose `## Owns` covers a file on `Outside Owns:`; cut the criteria that only wait for a person's one sentence into `decision` sub-issues and write the closing comment draft; close the reviewer's pane; `--closeout`. A re-prompted worker resumes at the step after the newest of `self-run`, `VERDICT`, `DECISIONS`, `REVIEW`. No branch is pushed and no pull request is opened: work reaches the base branch through `advance`.
_Avoid_: 收尾七步, 收尾六步, the seven closing steps, the closeout (for the sequence)
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`Audit`**:
The closing step that re-reads the whole ticket and every `## Read first` item, traces every criterion to its latest `EVIDENCE:`, and recounts `Counts:`.
_Avoid_: 交接前自审
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**closeout**:
`verify-ticket.py <n> --closeout <draft>`, the closing gate — the only place in the pipeline that closes a ticket or changes a label. It checks the draft against the ticket and the repository (first line, kinds, evidence behind every tick, `Counts:` agreeing with the first line, `VERDICT` on the ticket, `Post-verdict:` when HEAD moved, no uncommitted tracked changes and the branch containing its base commit). A draft that fails those conditions changes nothing, names the condition on stderr, and exits 1; the worker fixes the draft or the ticket and runs again. After an `ALL MET` draft is accepted it then runs `.mmw/target.json`'s optional `checks`; a failure posts `CHECKS FAILED` and does not close. On success it posts the comment (with `CHECKS OK <n>/<n>` when `checks` ran), removes `ready-for-agent`, and closes the ticket (`gh issue close --reason completed`, `CLOSED: #<n>`, `phase=closed`); on `HANDOFF REQUIRED` it posts the comment, hands the ticket back, and leaves it open (`phase=handoff`). `--check-only` is the dry run, printing `CLOSEOUT OK: #<n> draft passes every check`, and does not run `checks`. A command that would bypass it is refused by `hook.py`.
_Admitted_: closing gate
_Avoid_: 关票门, the gate at the end, 关票 (as a term)
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**host neutrality**:
A skill's text is one and the same for every host: no host is the default or preferred, nothing branches on a host's name, and differences in capability are written as natural language that judges by capability. The five hosts: `claude`, `codex`, `grok`, `cursor`, `pi`.
_Avoid_: 五宿主平权, host-neutral (as a name), 五个宿主
_Home_: `AGENTS.md`

**skills called by name**:
A skill's scripts are resolved by the agent holding that skill, from its own `SKILL.md`, as `scripts/…`; a caller names the skill and what it wants done, never an install path. Installing a skill is receiving its scripts, so the two cannot drift and the path is right on every host. The one exception is the `CHECK:` written into a ticket, which a shell runs with no agent in between, so its path is written in full.
_Home_: `AGENTS.md`

**the ticket is the only state**:
Every run reads the ticket afresh, writes at most one comment, and carries nothing to the next run; the ledger is thrown away; the ticket body is never edited — run state lives in the comments. The board keeps no state file for the same reason.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**The environment is yours; the repository is not**:
The verifier may install a dependency, move off a taken port, or find a connection string, and leaves the repository exactly as it found it; two identical `git status` outputs are the proof.
_Avoid_: the verifier's boundary
_Home_: `mmw-v2/agents/verifier/body.md`

**No pull request, and no push**:
No step of the pipeline reads a pull request and no branch is pushed; a ticket's work reaches the base branch through `advance`'s local merge, and the closing comment's `PR:` line is written in the future tense.
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
The unit the toolbox ships, one directory with a `SKILL.md`. This repository's own: `dispatch`, `verify-ticket`, `readable-docs`, `exe-release`, `manage-agents-md`, `claude-design-blocks`, `code-checkers`. From `mattpocock/skills`: `to-spec`, `to-tickets`, `implement`, `code-review`, `triage`, `wayfinder`, `domain-modeling`, `grilling`, `grill-me`, `grill-with-docs`, `prototype`, `research`, `resolving-merge-conflicts`, `setup-matt-pocock-skills`, `codebase-design`, `improve-codebase-architecture`, `tdd`, `diagnosing-bugs`, `ask-matt`, `wait-what`, `teach`, `to-questionnaire`, `writing-for-agents`, `handoff`, `wizard`. From `cathrynlavery/diagram-design`: `diagram-design`. A skill is named by its directory name; `the X skill` in prose, never `/X`.
_Home_: `mmw-v2/skills.txt`

**`SKILL.md`**:
A skill's entry file: the host loads the skill from it, and its location resolves the skill's `scripts/` and `references/`. It is symlinked from the source directory, so an edit takes effect on the next invocation; only its frontmatter **`description`** — the one thing a host scans at start — needs a new session. The frontmatter switch **`disable-model-invocation`** makes a skill user-invoked only; it is set or removed together with `policy.allow_implicit_invocation: false` in `agents/openai.yaml`, and this repository keeps it only on `readable-docs`, `setup-matt-pocock-skills`, `grill-me`, `handoff`, `wait-what`. A step in a skill closes with **`Done when`**, its completion test.
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

**`UPSTREAM.md`**:
The note written whenever upstream scripts are copied in without a subtree: source repository, commit, date, and which lines were changed.
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`

**`models.md`**:
The one table, one row per `(agent, host)`, five columns `agent | host | model | effort | launch arguments`, for every agent the pipeline sends out except the main agent — the only place a dispatched agent's model is written. It travels with the dispatch skill, one per machine, never into a consuming repository. `dispatch.sh` reads the rows with launch arguments; `assemble.py` reads the rows whose launch arguments are `—`. The three code-review axis subagents have no row. Editing rules are in `references/editing-models.md`.
_Avoid_: the table (for this), 模型表, 角色表
_Home_: `mmw-v2/skills/dispatch/models.md`

**`effort`**:
The `effort` column: the host's own name for the thinking level (`high`, `xhigh`, `medium`, …; one host's `high` is another's `xhigh`), passed as `{effort}`; Codex spells it `model_reasoning_effort`, Grok `reasoning_effort`; Cursor burns it into the model name, so its column is `—`.
_Admitted_: thinking level
_Avoid_: thinking effort, reasoning effort (in prose), 思考强度
_Home_: `mmw-v2/skills/dispatch/models.md`

**`launch arguments`**:
The fifth column: non-empty means the agent runs as its own Herdr session with `{model}`, `{effort}`, `{n}` substituted; `—` means a subagent.
_Avoid_: 启动参数
_Home_: `mmw-v2/skills/dispatch/models.md`

**`assemble.py`**:
`mmw-v2/agents/assemble.py`: builds each host's subagent file from `body.md` (the prompt text, single source), `agent.json` (`name`, `description`, the optional `sandbox`: `read-only` by default or `workspace-write`, honoured by Cursor, Codex, Grok), and `models.md`, into `agents/<name>/out/` — the **assembled subagent file**, one **per-host shell** around one body, because each host spells the model field differently. It writes only when something changed; `--check` verifies without writing; `install.sh` assembles first and then symlinks.
_Avoid_: 装配 (as a term), 成品, out/ file, 壳 (as a term)
_Home_: `mmw-v2/agents/assemble.py`

**`install.sh`**:
`mmw-v2/install.sh`, the only install entry. It installs four things: skill symlinks into `~/.agents/skills` and `~/.claude/skills`; assembled subagent files into each host's agent directory; hooks into each host's own configuration; the agent detection rule into `~/.config/herdr/agent-detection/`. It reads `skills.txt`, clears the retired locations, and prints one line per item with the prefixes `已装`, `装配`, `残留`, `退役`, `冲突`, ending with markers such as `HOOKS-INSTALLED`. **`install.sh --check`** looks and changes nothing: exit 0 when complete, 1 when something is missing or a stale link remains; it includes `assemble.py --check`, and `dispatch.sh run` runs it before a night. `MMW_V2_HOME` moves the install location for tests.
_Avoid_: the installer, 安装器, 安装入口 (as a term), 只看不动 (as a term)
_Home_: `mmw-v2/install.sh`

**hook**:
A program a host runs at an event. This repository installs two: `hook.py` (`pretool` on every host, `question` on the session hosts) and `turn.py` on the session hosts' lifecycle events, each registered in the host's configuration, with a **matcher** (the tool pattern, or the notification type) where the event takes one.
_Avoid_: 钩子 (for this sense)
_Home_: `mmw-v2/install.sh`

**`hook.py`**:
`scripts/hook.py` of the verify-ticket skill, the host-side enforcement of two rules, one per member of its `GATES`: **`pretool`** — when the host is about to run a shell command, it refuses `gh issue close` and label changes on the ticket named by `MMW_TICKET`, checks nothing, and points at `--closeout`; **`question`** — when the host is about to call its question tool in a session carrying `MMW_AUTONOMOUS=1`, it refuses and names the two ways out. No `MMW_TICKET`, no `pretool` gate; no `MMW_AUTONOMOUS`, no `question` gate. Its answer takes each host's shape (`permissionDecision: deny` on Claude Code and Codex, `decision: deny` on Grok, which clips the reason at 256 characters, `permission: deny` on Cursor); the verb in prose is **refuse**. It is symlinked, so editing it needs no reinstall.
_Admitted_: hook.py pretool
_Avoid_: the pretool gate, pretool 门, 关票 gate, 拦截 hook
_Home_: `mmw-v2/skills/verify-ticket/scripts/hook.py`

**`rule-at-moment.py`**:
`mmw-v2/hooks/rule-at-moment.py`, a Claude Code hook kept in the repository but not installed by `install.sh` (registered by hand as `~/.claude/hooks/rule-at-moment.py` if wanted): at the moment a ground rule of `~/.claude/CLAUDE.md` applies, it puts that rule's own text in front of the model — the file size before a `Read`, the next `offset` after a truncated one, rules 1, 3, 4, 6, 7 before a write, and rule 6 before an `Agent` call.
_Avoid_: 规则提醒 hook, 注入 hook
_Home_: `mmw-v2/hooks/rule-at-moment.py`

**`verify-ticket.py`**:
`scripts/verify-ticket.py` of the verify-ticket skill — one script carrying five jobs: `--lint`, the worker's own run `<n>`, the verifier's `--reverify`, `--preflight`, and `--closeout <draft>` (with `--check-only`; `--timeout <seconds>` raises the per-`CHECK:` limit for one run, and `TIMEOUT:` lines on the ticket raise it for every run). It is the only route by which a ticket closes; it reads the eight-section ticket shape; it writes the `phase` token at four moments; `--jobs` stays 1 because the branch, the ticket, and the working tree are shared. Exit 0, or 1 when `--closeout` refuses, or 2 when `--preflight` refuses. The skill's own text calls it `<engine>`.
_Avoid_: the engine, the ticket script, the script (for this)
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**`board.py`**:
`scripts/board.py` of the dispatch skill, the board's program: `--once [<spec>]` prints one table and exits; `[<spec>]` likewise; `--watch <spec>` is the one form that acts; `--advance-plan <spec>` prints the advance plan; `--worker-grades <spec>` prints one `GRADE <n> [<label> …]` line per `OPEN` ticket labelled `ready-for-agent`, blocked or not, for `run` to check before the night. It keeps no state file, re-reads the tracker and Herdr on every pane event or every `SNAPSHOT_INTERVAL`, holds one row per ticket, and appends one feed line per action through `say()` — never redrawing, and into the board log as well. Its constants: `MAX_HOURS = 4` (`--max-hours` overrides), `SNAPSHOT_INTERVAL = 60`, `FAILED_LIMIT = 3`, `FALLBACK_SECONDS = 600`, `TOKEN_TTL_MS = 86400000`. The skill's own text calls it `<board>`.
_Avoid_: wake budget
_Home_: `mmw-v2/skills/dispatch/scripts/board.py`

**ADR**:
An architecture decision record in `docs/adr/`, `0001-slug.md`, numbered current highest plus one, with `date` and `amends:` frontmatter and the sections Decision, Considered Options, Consequences. `docs/adr/README.md` is the hand-kept index, with the columns `改写了哪几份` and `被哪几份改写` for the amend relation and a translation table for the two earlier numberings. An ADR's Decision is a baseline source.
_Home_: `mmw-v2/upstream/skills/engineering/domain-modeling/ADR-FORMAT.md`

**research file**:
The Markdown file with citations the `research` skill leaves in the repository; one of the nine `## Sources` kinds; read to its last section as a `## Read first` item; its body is working material, not a baseline. `wayfinder:research` is the matching decision-ticket type.
_Home_: `mmw-v2/upstream/skills/engineering/research/SKILL.md`

### Values at a glance

| name | values |
| --- | --- |
| `phase` | `selfcheck` · `verify` · `implement` · `closed` · `handoff` · `closeout-rejected` |
| `agent_status` | `working` · `idle` · `done` · `blocked` · `unknown` |
| pane token | `ticket` · `kind` · `model` · `phase` · `ac` · `turn` · `turn_id` |
| `kind` token | `worker` · `reviewer` |
| host | `claude` · `codex` · `grok` · `cursor` · `pi` |
| `target.kind` | `electron` · `web-spa` · `web-server-rendered` · `chrome-extension` |
| mechanism `via` | `api` · `storage` |
| worker grade | `junior-worker` · `senior-worker` |
| `ABANDON:` kind | `failed` · `stuck` · `decision` |
| `ready-for-human` kind | `reaction` · `reach` |
| criterion state | `met` · `unmet` · `abandoned` |
| gate-check status line | `RUN` · `PASS` · `FAIL` |
| lint level | `ERROR` · `WARN` |
| `turn` | `ready` · `working` · `ended` · `failed:<error>` · `cancelled:<reason>` |
| `mmw board:` case | `ADVANCE` · `night over` · `STOPPED` · `TIME LIMIT` |
| `hook.py` gate | `pretool` · `question` |
| state role | `needs-triage` · `needs-info` · `ready-for-agent` · `ready-for-human` · `wontfix` |
| category role | `bug` · `enhancement` |
| `dispatch.sh` constants | `TOKEN_TTL_MS` · `PROMPT_TAKE_MS` · `WAIT_DEFAULT_SECONDS = 1800` · `MERGE_TRIES = 3` · `LABEL_TITLE_CHARS` · `BOARD_TAB_LABEL` · `MAIN_AGENT_NAME` · `DEFAULT_WORKER` |
| exit codes | `dispatch.sh` 0 / 1 (not reported ready in 120 s) / 2 (refused, nothing touched: the ticket's checks, a live session by the same name, `run`'s checks, or `advance` without the `.git` lock in `MERGE_TRIES` tries) / 3 (`advance` conflict) · `verify-ticket.py` 0 / 1 (`--closeout` refused) / 2 (`--preflight` refused) · `visual-parity.py` 0 / 1 (`DIFF`, `SHOWS-STATIC`) / 2 (`NEGATIVE CONTROL FAILED`, not ready, unreachable scene) · `wiring-check.py` 0 / 1 (`MISS`, `GREEN WITHOUT TRANSPORT`) / 2 (could not start, or `--negative` evaluated no observe) · `install.sh --check` 0 / 1 · `--lint` 0 unless an `ERROR` remains |
