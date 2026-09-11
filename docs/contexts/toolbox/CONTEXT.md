# Toolbox

MMW seen as a repository and as an install target: the skills it ships, the two subtrees and the one vendored copy it carries, where an install puts things on a machine, the prompts and hooks each host reads, the notes and ADRs that record why, and the rules about how skill text itself is written. Everything here is about the toolbox as an artifact, not about a night of work running through it.

How to read an entry: the bold line is the term's only name; a term whose name is a literal string that appears in a file, a command, or a comment is named by that string exactly (case, colon, and all). The definition says what the thing is and what sets it apart from its neighbours. `_Admitted_` lists the one other wording that may appear in prose. `_Avoid_` lists dead words: a sentence in this repository that uses one is wrong; an item followed by a note in parentheses says in which sense the word is dead. `_Home_` is the file whose text or code the definition is taken from; when this file and that one disagree, that one is right and this file is rewritten. An attribute that can be had by reading that file — a field list, an exit code, a command's switches, the branches of a behaviour — is not repeated here: an entry says what the term is and how it differs from its neighbours, and points at `_Home_` for the rest.

Vocabulary that belongs to one skill alone — `exe-release`'s release key, tiers, build machine and hooks; `claude-design-blocks`'s page kinds and helpers; `manage-agents-md`'s survey entries; `code-checkers`'s per-language checkers, their versions, and the file that silences a repository's existing errors; the design vocabulary of upstream skills such as `codebase-design` — is defined in that skill's own files and is not repeated here.

## Language

### Roles

**host**:
The command-line agent program a session runs on: one of `claude`, `codex`, `grok`, `cursor`, `pi`. It is the `host` field of a `models.json` row. Each host has its own install locations, its own place and format for a hook registration, its own name for the tool that puts a question on the screen, its own shape for the answer a hook gives it, and its own spelling of effort — `hook.py` decides nothing by host but the shape of its answer, and `hosts.json` holds how each one is started.
_Avoid_: 宿主, agent kind, form close key
_Home_: `mmw-v2/skills/drive-target/scripts/hook.py`

**user**:
The person. By day they work with the main agent on specs and tickets; they are the only reader of a `ready-for-human` ticket; `needs-triage` and `needs-info` wait on them; they are told when the night is over.
_Avoid_: human (for this), maintainer (in this repository's text), reporter (in this repository's text), 用户 (as a term)
_Home_: `docs/agents/triage-labels.md`

**subagent**:
An agent started inside another agent's session, holding its own context and answering back into that session. The toolbox ships no subagent definitions: `mmw-v2/agents/` and its assembler are gone, every host's `agents/` directory is a retired install location, and a skill that needs a subagent asks for the host's own general-purpose subagent — which runs on the model of the session that starts it, names no model and no thinking level, and has no `models.json` row. Nothing but its own instructions holds one to reading: only two of the five hosts take a tool list, so the binding sentence is the one at the top of its reference file, plus whatever restriction the call that starts it can carry. Results that must be written back to the ticket, read by another role, and openable by a person run as a session a runner starts (`dispatch.sh start`) instead; work that is only an internal split of the current step runs as a subagent. The three code-review axes run inside the reviewer session — as its subagents where the host can run them, as its own sequential passes where it cannot; the reviewer and the verifier themselves are sessions the worker starts, not its subagents.
_Avoid_: sub-agent, background agent, seat, 子代理 (as a term), native subagent, assembled subagent file
_Home_: `docs/adr/0015-no-custom-subagents.md`

**caller**:
Seen from inside a skill or subagent, the agent that invoked it and composed its packet. A caller names the skill and what it wants done, never an install path.
_Avoid_: 调用方 (for this)
_Home_: `AGENTS.md`

### Places

**MMW**:
This toolbox: the skills the user shares across hosts, repositories, and machines, together with the landing pipeline behind them (spec → ticket → a worker dispatched at night → a closed ticket) and this machine's task board. Only `mmw-v2/` is live. Three directories are frozen — not edited, not treated as fact, and no script inside them run: `archive/` is MMW's previous generation, `deprecated/` holds what v2 itself retired, and `docs/research/` holds read-only snapshots of third-party repositories alongside the research files. This repository is at the same time a consuming repository of its own pipeline.
_Admitted_: the toolbox
_Avoid_: 工具箱, this repository (as a name), 活层, live layer
_Home_: `AGENTS.md`

**consuming repository**:
The outside repository where real tickets are run, as distinct from the toolbox — although this repository is one of them, so that its own task board tickets run through the same pipeline. It holds the `.mmw/` acceptance runtime, its screen contracts and its `prototypes/`; it must hold a `DESIGN.md` before UI refinement. Neither machine-level file is ever placed in it: `models.json` lives under `MMW_HOME`, and `hosts.json` travels with the dispatch skill.
_Avoid_: consumer repo, 消费仓库, the project (for this), the repo (for this)
_Home_: `AGENTS.md`

**repository root**:
`git rev-parse --show-toplevel`: the fixed working directory of every `CHECK:` unless a `CWD:` moves it, and where `CONTEXT.md` and `AGENTS.md` live.
_Avoid_: repo root, 仓库根
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**subtree**:
How an upstream repository is carried inside this one: `git subtree pull --prefix … --squash`. `mmw-v2/upstream/` is `mattpocock/skills`; `mmw-v2/upstream-diagram-design/` is `cathrynlavery/diagram-design`. Both are editable, and a change to a skill inside one requires a merge-note. `gate-check/` is not a subtree: it was copied in whole, `git subtree pull` does not reach it, and its provenance is `UPSTREAM.md`.
_Home_: `mmw-v2/merge-notes/README.md`

**upstream**:
The source project of a subtree. Its own `AGENTS.md`, `CLAUDE.md`, and `CONTEXT.md` are left untouched — only `mmw-v2/upstream/` carries all three — and any passage no merge-note covers is taken as upstream wrote it, which is also the rule for resolving a conflict a merge-note does not cover.
_Avoid_: 上游票号 (that is a blocker)
_Home_: `mmw-v2/merge-notes/README.md`

**unlazy**:
The repository `gate-check/` was copied from (`https://github.com/Leonxlnx/unlazy`, commit `da0b00a3`, MIT), vendored 2026-08-29, with the snapshot it was taken from kept at `docs/research/code-landing-refs/unlazy/`. It is not a subtree; what was taken as-is, what was edited, and what was left behind are recorded in `UPSTREAM.md`.
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`

**source directory**:
One of the three directories in this repository a host's skill symlink points straight at (`mmw-v2/skills/`, `mmw-v2/upstream/skills/`, `mmw-v2/upstream-diagram-design/skills/`), so an edit takes effect on the next call. `install.sh` knows a link is its own because `readlink` lands inside one of them, matched by path segment — so any checkout of this repository counts, and whichever checkout runs `install.sh` takes over the batch.
_Avoid_: 源目录 (as a term; the merge-note field `源目录：` is a literal), 仓库源目录
_Home_: `mmw-v2/install.sh`

**`~/.agents/skills`**:
The host-neutral install location `install.sh` creates unconditionally on every machine; Codex, Cursor, Grok, and Pi scan it. `~/.claude/skills` is the second copy, because Claude Code scans only that and is skipped when that host is not installed. Both hold symlinks straight to the source directory. The four per-host locations `~/.codex/skills`, `~/.pi/agent/skills`, `~/.cursor/skills`, `~/.grok/skills` are retired.
_Avoid_: 通用位置, 中立目录, 用户级目录
_Home_: `docs/adr/0006-skills-install-to-neutral-dir.md`

**symlink**:
What `install.sh` makes: skills into the two install locations; `~/.claude/CLAUDE.md` to `prompt/shared.md` and `~/.claude/rules/mmw-claude.md` to `prompt/hosts/claude.md`; `~/.local/bin/paseo` to the Paseo CLI. `hook.py` and `turn-guard.py` are not linked anywhere: each host's configuration names them at their path under `~/.agents/skills`, which is already a link back into the repository, so editing a script needs no reinstall. A symlink is not a copy — the host reads the repository file — and whichever checkout runs `install.sh` takes over the batch and is recorded in `~/.mmw/installed-root`.
_Avoid_: agent detection rule
_Home_: `mmw-v2/install.sh`

**stale link**:
A symlink that points back into this repository but is not on the list, or a last-generation link left in a retired location. `install.sh --check` prints `残留` and returns 1; `install.sh` removes it. A hook registration is claimed the same way — a command naming a script under `~/.agents/skills` is this repository's — and one this run does not install is swept out with it.
_Avoid_: 残留 (as a term; the printed prefix is a literal)
_Home_: `mmw-v2/install.sh`

**retired**:
The state of a skill or subagent moved to `deprecated/` (unchanged, not treated as fact), and of an install location that is no longer a target though its host still scans it. The retired locations are the four per-host `skills/` directories and the six subagent directories — `~/.claude/agents`, `~/.codex/agents`, `~/.pi/agent/agents`, `~/.cursor/agents`, `~/.grok/agents`, `~/.grok/roles`. `install.sh` prints `退役` when it clears its own links from one. A frozen directory is not retired: `archive/`, `deprecated/` and `docs/research/` are kept as they are, while a retired location is actively emptied.
_Avoid_: 退役 (as a term; the printed prefix is a literal)
_Home_: `AGENTS.md`

**issue tracker**:
GitHub Issues for this repository, every operation through `gh`. It is the only store of fact and state: parent–child relations, blocking links, the frontier, and claims exist only here. Its operations — Create, Read, List, Comment, Apply and remove labels, Close, Re-parent, Transfer, Read a PR, List external PRs, Claim, Resolve — are each one `gh` command in `docs/agents/issue-tracker.md`; `publish to the issue tracker` means create a GitHub issue; `PRs as a request surface` is `no`. Every list read is a whole list: `gh issue list` stops at 30 without `-L` and a `gh api` list endpoint returns one page without `--paginate`, both in silence, so every command that reads a set carries `-L 500` or `--paginate` with `?per_page=100` — except a tree, which `tree.py` reads in one query.
_Admitted_: the tracker
_Avoid_: backlog (for this), 真 tracker, GitHub Issues (as a term)
_Home_: `docs/agents/issue-tracker.md`

**`gh`**:
The CLI every issue-tracker operation goes through. Every script that shells out to it drops `CLICOLOR` and `CLICOLOR_FORCE` from the environment first, because Grok Build hands its agents `CLICOLOR_FORCE=1` and under it `gh` writes ANSI escapes into output meant to be parsed; the runner binaries are called the same way.
_Home_: `docs/agents/issue-tracker.md`

**`docs/agents/`**:
The three files `setup-matt-pocock-skills` seeds once: `issue-tracker.md`, `triage-labels.md`, `domain.md`. `triage-labels.md`'s `## What carries a label here` section is this repository's own and a re-run would overwrite it; the other two differ from the seeds only in the passages the merge-note records. The root `AGENTS.md` points at all three from its External References table rather than from the seeded `## Agent skills` block, whose `### Domain docs` sub-block this repository no longer carries; this repository is multi-context: the root `CONTEXT-MAP.md` and one `CONTEXT.md` per context under `docs/contexts/`, with every ADR system-wide in `docs/adr/`.
_Avoid_: tracker 配置, 单 context (as a term)
_Home_: `mmw-v2/merge-notes/setup-matt-pocock-skills.md`

**`CONTEXT.md`**:
The vocabulary of one bounded context, at `docs/contexts/<name>/CONTEXT.md`; the root `CONTEXT-MAP.md` lists the contexts, where each lives and how they relate, and a term is defined in exactly one of them. `mmw-v2/upstream/CONTEXT.md` is upstream's own and is not part of it. `domain-modeling` writes it; a worker reads the consuming repository's own before writing code, and anything naming a domain concept — an issue title, a hypothesis, a test name — uses the term as defined here and does not drift to a word its `_Avoid_` line lists. It doubles as the interface record — command signatures, constant tables, fixed output shapes — so a definition may run longer than two sentences; but an entry that says less than its `_Home_` file is not a defect, and one that says more is. A definition that disagrees with its `_Home_` file is wrong and the entry is the side that gets fixed: the systematic update walks every entry, opens its `_Home_`, and rewrites the entry from what that file says or does.
_Avoid_: 词表, glossary, domain glossary, 接口契约, root CONTEXT.md (for this repository)
_Home_: `docs/agents/domain.md`

**`AGENTS.md`**:
A repository's agent instruction file, root plus nested pairs, written to the one fixed format the `manage-agents-md` skill defines: an identity paragraph, then Package Manager, Commands, External References, Key Conventions and Gotchas (headings translated into the file's own language), then one `<important if="…">` block per kind of work, and last the English sentence telling a reader to look for a nested `AGENTS.md` before working in a subdirectory. A root file carries nothing else — no directory map, no environment list, no list of installed skills, no metadata header; a nested file carries only what differs from the root. `CLAUDE.md` beside it holds only the line `@AGENTS.md` and any other `@` imports.
_Avoid_: bridge (for this)
_Home_: `mmw-v2/skills/manage-agents-md/references/write.md`

### The toolbox

**skill**:
The unit the toolbox ships, one directory with a `SKILL.md`. This repository's own: `dispatch`, `verify-ticket`, `verdict`, `advisor`, `drive-target`, `align-screens`, `exe-release`, `manage-agents-md`, `claude-design-blocks`, `code-checkers`. From `mattpocock/skills`: `to-spec`, `to-tickets`, `implement`, `code-review`, `triage`, `wayfinder`, `domain-modeling`, `grilling`, `grill-me`, `grill-with-docs`, `prototype`, `research`, `resolving-merge-conflicts`, `setup-matt-pocock-skills`, `codebase-design`, `improve-codebase-architecture`, `tdd`, `diagnosing-bugs`, `ask-matt`, `wait-what`, `teach`, `to-questionnaire`, `writing-for-agents`, `handoff`, `wizard`. From `cathrynlavery/diagram-design`: `diagram-design`. A skill is named by its directory name; `the X skill` in prose, never `/X`.
_Home_: `mmw-v2/skills.txt`

**`SKILL.md`**:
A skill's entry file: the host loads the skill from it, and its location resolves the skill's `scripts/` and `references/`. It is symlinked from the source directory, so an edit takes effect on the next invocation; only its frontmatter **`description`** — the one thing a host scans at start — needs a new session. A skill this repository wrote carries no host-side manifest beside it and only `name` and `description` in its frontmatter, so its name and description have one authority. The frontmatter switch **`disable-model-invocation`** makes a skill user-invoked only; on an upstream skill it is set or removed together with `policy.allow_implicit_invocation: false` in `agents/openai.yaml`, and this repository keeps it only on `setup-matt-pocock-skills`, `grill-me`, `handoff`, `wait-what`. A step in a skill closes with **`Done when`**, its completion test.
_Avoid_: 技能正文 (as a term), 用户触发开关, user-invoked (as a name), completion criterion
_Home_: `AGENTS.md`

**`skills.txt`**:
The one list deciding which skills are installed: `<root>/<name>` lines under `self/`, `engineering/`, `productivity/`, `dd/`, with `#` lines and blank lines ignored; `install.sh` reads it, and a link in an install location that points back into this repository without being on the list is swept.
_Avoid_: 名单 (as a term)
_Home_: `mmw-v2/install.sh`

**`tests/run.sh`**:
The test entry point of one skill or one subsystem, the own-script layer, one directory each under `mmw-v2/tests/` — ten of them: `verify-ticket`, `drive-target`, `align-screens`, `dispatch`, `exe-release`, `manage-agents-md`, `claude-design-blocks`, `board`, `liveness`, `relay`; `advisor`, `code-checkers` and `verdict` have none. There is no overall entry point and no CI: each is run by hand, and each one's header says what it tests and what runtime it needs. They live only in a checkout and are never symlinked into a host; each reaches its subject by counting two levels back to `mmw-v2/` and loading the script by path. gate-check's own tests are the vendored-script layer and stay in its own directory.
_Home_: `mmw-v2/tests/AGENTS.md`

**merge-note**:
One note per changed upstream skill in `mmw-v2/merge-notes/`: which passages this repository changed, why, and how to choose when upstream touches them again — intent, not diff. Its fixed parts are Chinese literals: `源目录：`, `## 逐段意图`, the table columns `段落` and `我们的意图`, `收上游` and `弃上游`. `merge-notes/README.md` indexes them and gives the upstream-pull procedure, plus the two rules every note assumes rather than repeats — the paired `disable-model-invocation` switch and the three host-neutral rewrites; gate-check has `UPSTREAM.md` instead.
_Admitted_: 说明 (in `merge-notes/README.md`)
_Home_: `mmw-v2/merge-notes/README.md`

**downstream-note**:
One note per change in this repository that invalidates a consuming repository's existing screen contract, ticket `CHECK:`, or `.mmw/target.json` — what changed, which of those classes (plus target trees, which go stale with the screen contract) go stale, and how to migrate — the opposite of a merge-note; `mmw-v2/downstream-notes/README.md` says which changes require one and indexes them. Its fixed parts are Chinese literals in this order: `## 改了什么`, `## 哪些产物失效`, `## 怎么迁`; its filename is the number of the ticket that caused the change plus a slug.
_Admitted_: 说明 (in `downstream-notes/README.md`)
_Home_: `mmw-v2/downstream-notes/README.md`

**`UPSTREAM.md`**:
The note written whenever upstream scripts are copied in without a subtree: source repository, commit, date, licence, which files are byte-identical to the snapshot, which were edited and how, and which were deliberately left behind. It is the one thing a skill directory carries that the agent holding the skill does not read — it is written for whoever next compares against upstream, whose only clue is the directory itself, and it covers the whole of `mmw-v2/skills/verify-ticket/scripts/gate-check/`, its own `tests/` included.
_Home_: `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`

**`models.json`**:
The versioned machine-level dispatch configuration at `MMW_HOME/models.json`, defaulting to `~/.mmw/models.json`. It holds the night's `runner` and one row per dispatched agent — `junior-worker`, `senior-worker`, `reviewer`, `verifier`, `advisor` — and is the only place a dispatched agent's model is written. `models.py config` and the task board share its validation, its lock and its whole-file atomic replacement. `dispatch.sh start` reads it fresh. `install.sh` creates it from `hosts.json` defaults when absent, or imports and deletes the retired Markdown file once; it never overwrites an existing JSON file. The main agent and the code-review axis subagents have no row.
_Avoid_: the table (for this), model table, role table, launch arguments, 活表, 模型表, 角色表
_Home_: `~/.mmw/models.json`

**`effort`**:
The `effort` field of a `models.json` row: the everyday thinking level (`high`, `xhigh`, `medium`, …). Every row needs one, and what a host does with it is `hosts.json`'s to say. Grok, Claude and Codex list the values they accept and take it as a flag of their own CLI; pi has no CLI entry, so it takes it only as a Paseo thinking option. Cursor takes it in neither place — `effort_in_model` is true there, so the level is part of the model id chosen in the Cursor app and `start` only selects among the pairs `cursor-agent models` already lists. On Paseo, effort becomes the `--thinking` value of `paseo run`, which for Cursor is only on or off.
_Admitted_: thinking level
_Avoid_: thinking effort, reasoning effort (in prose), 思考强度
_Home_: `~/.mmw/models.json`

**permissions**:
How a dispatched session is started: all tools granted. It is not a field in `models.json`. Each host's spelling lives in `hosts.json`, in its `cli.argv` or its `paseo.settings` (`bypassPermissions`, Codex's `--dangerously-bypass-approvals-and-sandbox` and `full-access`, Grok's `--always-approve`, Cursor's `--force` and `auto_accept`). There is no read-only value: no host has a mode that both keeps a session to reading and lets it finish a turn on its own, so an agent that must not write is a subagent, held to reading by what it is told to do and by whatever restriction the call that starts it can carry.
_Avoid_: launch arguments
_Home_: `mmw-v2/skills/dispatch/hosts.json`

**`models.py`**:
`mmw-v2/skills/dispatch/scripts/models.py`, the shared reader and writer of `models.json` and the reader of `hosts.json`, which travels with the dispatch skill and so is present on every host. It resolves everyday names against a catalog — Paseo's when tonight's runner is Paseo, otherwise the host's own CLI — and turns a saved row into the arguments a runner starts the host with, so the task board, `install.sh --check` and `dispatch.sh start` cannot disagree; it also answers which runner tonight uses, ending in a default. It runs no runner command itself: those belong to `runners/<runner>.sh`.
_Home_: `mmw-v2/skills/dispatch/scripts/models.py`

**`MMW_CATALOG_MODE`**:
Which catalog `models.py` resolves a `models.json` row's everyday model name against: `paseo` asks Paseo's provider catalog, `cli` asks the host's own CLI, and `cli` is the default when the variable is unset. `dispatch.sh` exports it from tonight's runner — `paseo` for Paseo, `cli` for every other — so one host is never asked of two sources in one night, which is how a saved name could validate on the task board and then fail at start. Only tests set it by hand (or set `MMW_HOST_CATALOG` to skip the binaries), and a runner strips it from a session's environment before running, so a suite run from inside a worker session does not inherit that night's answer.
_Avoid_: catalog switch, 目录来源 (as a term)
_Home_: `mmw-v2/skills/dispatch/scripts/models.py`

**`install.sh`**:
`mmw-v2/install.sh`, the only install entry. It installs eight things: skill symlinks into `~/.agents/skills` and `~/.claude/skills`; hooks into each host's own configuration (`hook.py` and `turn-guard.py`, with Codex's `trusted_hash` lines written into `~/.codex/config.toml`); user-level prompts (`~/.claude/CLAUDE.md` a symlink to `prompt/shared.md` and `~/.claude/rules/mmw-claude.md` one to `prompt/hosts/claude.md`, Codex, Pi and Grok each a file `prompt/render.py` writes); a launchd task that re-renders those three when the source changes; the `com.mmw.board` LaunchAgent that keeps `supervisor.py` running; Paseo configuration (`~/.local/bin/paseo`, two providers in `~/.paseo/config.json`, `worktrees.root`); Orca worktree configuration, only where `orca` is installed (every Orca setup's `worktree-base-path` is `.worktrees`, and each repository's `externalWorktreeVisibility` is `show`); the `nowledge-mem` entry in `~/.cursor/mcp.json`. It does not write Agent profiles; leftover generated profiles (notes containing `from models.md`) are reported as `残留`. When `models.json` is absent, install writes the `hosts.json` defaults or imports and deletes the retired Markdown file; an existing JSON file is untouched. It reads `skills.txt`, clears the retired locations, records the checkout it ran from in `~/.mmw/installed-root`, and prints one line per item with the prefixes `已装`, `残留`, `退役`, `冲突`, ending with markers such as `HOOKS-INSTALLED`. **`install.sh --check`** looks and changes nothing: exit 0 when complete, 1 when something is missing or stale; run from a different checkout it hands over to the `install.sh` of the checkout `~/.mmw/installed-root` names, which checks without taking over. It validates the task board LaunchAgent, every saved row against the selected runner's catalog, and each runner adapter's `# MMW_USES:` lines against the binary on `PATH`, printing `没查` when it could not read what the binary accepts and `不一致` when a command or flag is gone. `dispatch.sh check` runs it before a night. `MMW_V2_HOME` moves the whole install location for tests and suppresses `launchctl` and `paseo reload`.
_Avoid_: the installer, 安装器, 安装入口 (as a term), 只看不动 (as a term)
_Home_: `mmw-v2/install.sh`

**`# MMW_USES:`**:
A comment line in a runner adapter's header declaring one command that adapter runs: `# MMW_USES: <subcommand> [--flag …]`, the bare words naming the subcommand and the `-`-prefixed tokens its flags. Together those lines are the authoritative declaration of everything the adapter asks of its binary — nothing at run time reads them, and an adapter carrying none is reported rather than passed. `install.sh --check` reads them, opens that subcommand's own help page on the binary now on `PATH`, and prints `不一致` for a declared flag the help page does not have and `没查` when the help page could not be read or a line names no command, so a runner that changed its CLI under us is found before a night rather than during one.
_Avoid_: uses line, 声明行 (as a term)
_Home_: `mmw-v2/install.sh`

**`~/.mmw/installed-root`**:
The file a full `install.sh` run writes with the absolute path of the checkout it ran from, so the machine knows which checkout is the installed one. `--check` run from any other checkout prints `装自 <that one>` and hands the whole check over to that checkout's own `install.sh --check`: a frozen checkout serves the hosts while the night that rebuilds the toolbox runs in another, and checking one version's files with another version's checking code is what would break. It hands over the check only; nothing about it ever takes over an install.
_Avoid_: install marker, 安装来源文件
_Home_: `mmw-v2/install.sh`

**`MMW_V2_HOME`**:
The variable that moves the whole install location: every path `install.sh` reads or writes goes under it instead of `$HOME`. Under it the run also writes and checks the launchd plist without ever calling `launchctl`, and runs no `paseo reload`, so a suite verifies the same definitions without touching the machine's services. It exists for tests alone — `install.sh`'s own, and `prompt/tests/run.sh`, which runs `render.py` against a throwaway home under it. It is not `MMW_HOME`, which is where `models.json` and the leases live.
_Avoid_: install prefix, 测试家目录
_Home_: `mmw-v2/install.sh`

**`--tools`**:
The one flag `verify-ticket.py`, `dispatch.sh` and `lint_contract.py` share: a directory holding the scripts of another skill, repeatable. For `verify-ticket.py` and `dispatch.sh` it is an override — each resolves its sibling skills' `scripts/` from its own location (the drive-target skill's for the judges and `lease.py`, the verify-ticket skill's for `verify-ticket.py` and `events.py`) and searches what `--tools` gives first. `verify-ticket.py` puts the directories in force on the `PATH` of every `CHECK:`, so a criterion names a judge bare and carries no install location; a ticket naming a judge that neither those directories nor `PATH` holds is refused before anything runs, exit 2 with the script named on stderr, because a `command not found` reads exactly like a criterion that ran and failed. `dispatch.sh advance` passes them on to the `start` it runs. For `lint_contract.py` it stays required, since that script loads `extract_skeleton.py` and the driver through it: missing, it prints its usage and exits 2.
_Avoid_: tools dir, 工具目录 (as a term), skills root
_Home_: `mmw-v2/skills/drive-target/SKILL.md`

**hook**:
A program a host runs at an event. This repository installs two, registered in each host's own configuration with a **matcher** (the tool pattern) where the event takes one: `hook.py` of the drive-target skill, and `turn-guard.py` of the dispatch skill on each host's turn-end event. Four hosts take JSON; pi takes an extension file written whole. Every registration names the script at its path under `~/.agents/skills`, which is already a symlink into the repository.
_Avoid_: 钩子 (for this sense), turn.py
_Home_: `mmw-v2/install.sh`

**`hook.py`**:
`scripts/hook.py` of the drive-target skill, the host-side enforcement of three refusals across its two `GATES`. **`pretool`** — when the host is about to run a shell command — refuses two things and checks nothing: a command that would end a process (`kill`, `pkill`, `killall`, `killall5`, or an `xargs … kill`, taken as the first word of a piece the shell would run on its own), and a command that would take the ticket out of the agent queue by hand, which is `gh issue close` or a `gh issue edit` removing `ready-for-agent` or adding `needs-triage` or `ready-for-human`, pointing at `--closeout` instead. **`question`** — when the host is about to call its own question tool in a ticket worktree — refuses and names the two ways out. It refuses rather than checks, because a worker typing `gh issue close` has by definition not been through `--closeout`. Whether a session is governed is the working directory's basename `issue-<n>`, read from `getcwd` or, where the host runs its hooks from elsewhere (Cursor runs them from `~/.cursor` and sends an empty `cwd`), from `PASEO_AGENT_CWD`; any other basename is no gate, and nothing is asked of any runner. Its answer takes each host's shape (`permissionDecision: deny` on Claude Code and Codex, `decision: deny` on Grok, `permission: deny` on Cursor, `block: true` on pi) and it exits 0 either way; the verb in prose is **refuse**. Cursor imports Claude Code's hooks with no off switch, so the Claude-registered copy stands down when the payload carries Cursor's own `cursor_version` — read off the payload, never off the environment. It is symlinked, so editing it needs no reinstall.
_Admitted_: hook.py pretool
_Avoid_: the pretool gate, pretool 门, 关票 gate, 拦截 hook, MMW_TICKET, MMW_AUTONOMOUS
_Home_: `mmw-v2/skills/drive-target/scripts/hook.py`

**`rule-at-moment.py`**:
`mmw-v2/hooks/rule-at-moment.py`, a Claude Code hook kept in the repository but not installed by `install.sh` — to use it, symlink it to `~/.claude/hooks/rule-at-moment.py` and register it by hand for `PreToolUse`, `PostToolUse` and `PostToolUseFailure`. It writes no text of its own: at the moment a ground rule of `~/.claude/CLAUDE.md` applies, it cuts that numbered rule out of the file and puts it in front of the model — rule 2 before a `Read` (with the file's line count, byte count and token estimate, and with `offset`, how many lines remain), before a `Grep`, `WebFetch` or `Bash`, and again after a truncated result with the next `Read` to make; rules 1, 3, 4, 6, 7 before a write; rule 6 before an `Agent` call; rule 5 on a failed call. Anything unexpected — no `CLAUDE.md`, a missing heading, unreadable stdin — is a silent exit 0: it only ever adds a note and never breaks a call.
_Avoid_: 规则提醒 hook, 注入 hook
_Home_: `mmw-v2/hooks/rule-at-moment.py`

**`verify-ticket.py`**:
`scripts/verify-ticket.py` of the verify-ticket skill — one script carrying eleven jobs: `--lint`, the worker's own run `<n>`, `--reverify` (the verifier's, or the main agent's with `--actor main`), `--preflight`, `--closeout <draft>` (with `--check-only`; `--timeout <seconds>` raises the per-`CHECK:` limit for one run, and `TIMEOUT:` lines on the ticket raise it for every run), `--decisions <file>`, `--touched`, `--draft <out-file>`, `--sub-issue <kind> <file>`, the reviewer's `--review <file>`, the verifier's `--verdict "<one line>" --model <model>`. Two jobs at once is a usage error. It is the only route by which a ticket closes; it reads the `<issue-template>` shape; nothing is cached and no file is left behind, and gate-check's `--jobs` stays 1 because the branch, the ticket, and the working tree are shared. Exit 0, or 1 when `--closeout` refuses or `--sub-issue` opened the child but could not write its `child.opened`, or 2 when `--preflight`, `--decisions`, `--touched`, `--draft`, `--sub-issue`, `--review` or `--verdict` refuses. The two runs of the criteria also exit 3 when they waited for a product slot and none came free, and 4 when the `ticket.checked` recording them could not be written. The skill's own text calls it `<engine>`.
_Avoid_: the engine, the ticket script, the script (for this)
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**--decisions**:
`verify-ticket.py <n> --decisions <file>`: checks the file has the two sections `Decisions I made on my own` and `Outside Owns` and no others, and that `Outside Owns` matches the `Outside Owns:` line of the newest `ticket.checked` of run `self`, then posts it as the `worker.decided` event, first line `DECISIONS`. Exit 2 and nothing posted if the ticket already carries a `worker.decided` event, if the ticket has no run of the worker's own yet, or if a section is missing or extra — the reason is named on stderr.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**--touched**:
`verify-ticket.py <n> --touched`: reads the `Outside Owns:` files of the newest `ticket.checked` of run `self` and posts a `worker.touched` event on each open sibling whose `## Owns` covers one of them, so the ticket that owns the file learns somebody else wrote in it. Exit 2 if there is no `reviewer.reported` event, because the review is what says whether those files should have been touched at all. No such file: nothing posted, exit 0.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**--draft**:
`verify-ticket.py <n> --draft <out-file>`: writes the closing-comment skeleton to `<out-file>`, recounted from the ticket and the newest own run, with `skipped:` and `Decisions I made on my own` left as `<fill>` and `Sub-issues opened:` already filled from this ticket's children. Nothing lands on the ticket. `--closeout` refuses the skeleton until those two are filled. Exit 2 with no file written when the newest `worker.started` carries no `into`.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**--sub-issue**:
`verify-ticket.py <n> --sub-issue <kind> <file>`: takes a kind and a file whose first line is the title, opens a new issue labelled `needs-triage` and `mmw:child` (creating the layer label where the repository lacks it), parented to this ticket, its body's first line ``A `<kind>` child of #<n>.``, and posts `child.opened` on this ticket — the ticket's events are where its children are counted. `kind` is one of the five child kinds: `finding`, `contract`, `deferred`, `decision`, `fault`. Empty file, unknown kind, or a `mmw:child` label the repository lacks and will not let be created: exit 2, nothing opened. Exit 1: the child is open and its `child.opened` could not be written, so opening it again would make two.
_Home_: `mmw-v2/skills/verify-ticket/references/sub-issues.md`

**`tree.py`**:
`scripts/tree.py` of the verify-ticket skill (`python3 <that script> <issue> --root map|spec|ticket`, default `spec`): the tree under a map, a spec or a ticket read in one GraphQL query, at fixed page sizes — 50 specs under a map, 100 tickets under a spec, 50 children under a ticket — each issue with its number, title and state, and each issue with a layer below it with GitHub's count of that layer. `status.py` and `--lint` read a spec's batch through it. A list shorter than the count GitHub gives for it, or an answer carrying `errors`, is refused (exit 2) and nothing is returned, rather than read as the whole: a page left unread raises no error of its own.
_Avoid_: sub_issues endpoint (for reading a tree), tree walk
_Home_: `docs/agents/issue-tracker.md`

**ADR**:
An architecture decision record in `docs/adr/`, `0001-slug.md`, numbered current highest plus one. Its shape here: `date` and `amends` frontmatter, a one-line `# ` heading that is the decision itself, a paragraph of prose under it, zero to two freely titled sections, `## Considered Options`, `## Consequences` — and no `## Decision` section, because the decision is the heading plus that paragraph, and that pair is what a citation of the ADR cites. `docs/adr/README.md` is the hand-kept index, with the columns `改写了哪几份` and `被哪几份改写` for the amend relation and a translation table for the two earlier numberings. An ADR's decision is a baseline source.
_Home_: `docs/adr/README.md`

**research file**:
The Markdown file with citations the `research` skill leaves in the repository, written against primary sources and saved wherever the repository already keeps such notes; one of the nine `## Sources` kinds; read to its last section as a `## Read first` item; its body is working material, not a baseline. `wayfinder:research` is the matching decision-ticket type.
_Home_: `mmw-v2/upstream/skills/engineering/research/SKILL.md`

### Working discipline

**host neutrality**:
A skill's text is one and the same for every host: no host is the default or preferred, nothing branches on a host's name, and differences in capability are written as natural language that judges by capability — "a host that cannot hold a turn open", "a host that can start a subagent". The five hosts: `claude`, `codex`, `grok`, `cursor`, `pi`. The three rewrites this forces on upstream text — a tool name, a slash invocation, a session-management command — are in `merge-notes/README.md`.
_Avoid_: 五宿主平权, host-neutral (as a name), 五个宿主
_Home_: `AGENTS.md`

**runner neutrality**:
A skill's text is one and the same for every runner: nothing branches on a runner's name, and a difference in what runners can do is written as that capability. Which runner runs tonight is chosen by `models.py runner`, whose last step is a default; the text states that choice and assumes nothing past it. A runner's own commands are written only in its adapter, whose `# MMW_USES:` lines are the authoritative declaration of every command it calls. A skill's `description` names no runner, since every host scans it into its system prompt: a runner that cannot start is refused by one stderr line of the script at run time, never by a precondition in the `description`.
_Avoid_: runner-neutral (as a name)
_Home_: `AGENTS.md`

**skills called by name**:
A skill's scripts are resolved by the agent holding that skill, from its own `SKILL.md`, as `scripts/…`; a caller names the skill and what it wants done, never an install path. Installing a skill is receiving its scripts, so the two cannot drift and the path is right on every host. The `CHECK:` written into a ticket is run by a shell with no agent in between, and it names no path either: `verify-ticket.py` resolves the drive-target skill's `scripts/` through `--tools` and puts it on that shell's `PATH`, and refuses the whole run with exit 2 when a judge the ticket names is in none of those directories.
_Home_: `AGENTS.md`

**silence is never a pass**:
The question a gate is judged by when it is added or changed: *if this ran and did nothing at all, would anyone find out?* A gate that neither does its job nor says so reads exactly like one that passed, so everything here that can refuse must do three things — name the fact it checked so the reader can go look, give the one way out rather than a list of options, and fail loudly when it could not run at all, because "could not check" and "checked, it is fine" are two answers and only one of them is silence. The three-part shape of a refusal message itself is `refusal.py`.
_Avoid_: 沉默不算通过, fail-safe (for this)
_Home_: `docs/adr/0008-silence-is-never-a-pass.md`

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

### Values at a glance

| name | values |
| --- | --- |
| host | `claude` · `codex` · `grok` · `cursor` · `pi` |
| `hook.py` gate | `pretool` · `question` |
