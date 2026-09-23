# Toolbox

MMW seen as a repository and as an install target: the skills it ships, the three subtrees it carries, where an install puts things on a machine, the prompts and hooks each host reads, and the notes and ADRs that record why. Everything here is about the toolbox as an artifact, not about a run of the pipeline through it.

How to read an entry: the bold line is the term's name, and a term that is a literal string in a file, a command or a comment is named by that string exactly. The definition says in one or two sentences what the thing is and how it differs from its neighbours. `_Avoid_` lists wordings that name the concept less precisely in this repository's own text, each with the sense in which it is avoided. `_Home_` is the file that states the fact; an entry does not repeat what can be read there (a field list, an exit code, a command's switches, the branches of a behaviour), and when the two disagree, `_Home_` is right.

Vocabulary that belongs to one skill alone — `exe-release`'s release manifest, tiers, build machine and hooks; `design-pages`'s `pull_design.py` switches and exit codes and the style rules in `template-project-claude-md.md`; `manage-agents-md`'s survey entries; `code-checkers`'s per-language checkers, their versions, and the file that silences a repository's existing errors; the design vocabulary of upstream skills such as `codebase-design` — is defined in that skill's own files and is not repeated here. The design-pages entries and the page conventions are defined in `docs/contexts/ui-acceptance/CONTEXT.md`.

## Language

### Roles

**host**:
The command-line agent program a session runs on, one of `claude`, `codex`, `grok`, `cursor`, `pi`: the `host` field of a `models.json` row. Distinct from the **runner**, which starts the session and keeps it running.
_Home_: `mmw-v2/skills/dispatch/hosts.json`

**user**:
The person who owns the products and works with the main agent on specs and tickets. The user is the only reader of a `ready-for-human` ticket, and `needs-triage` and `needs-info` wait on the user.
_Home_: `docs/agents/triage-labels.md`

**subagent**:
An agent started inside another agent's session, holding its own context and answering back into that session; a skill that needs one asks for the host's own general-purpose subagent, which runs on the model of the session that starts it and has no `models.json` row. Distinct from a session a runner starts with `dispatch.sh start`, which writes its result to the ticket; a code-review axis runs as a subagent of the reviewer session where the host can run one.
_Home_: `docs/adr/0015-no-custom-subagents.md`

### Places

**MMW**:
This toolbox (the toolbox): the skills the user shares across hosts, repositories and machines, together with the landing pipeline behind them (spec → ticket → a dispatched worker → a closed ticket) and the task board. Only `mmw-v2/` is live; `archive/`, `deprecated/` and `docs/research/` are frozen.
_Home_: `AGENTS.md`

**consuming repository**:
A repository whose real tickets run through the pipeline and which holds the `.mmw/` acceptance runtime, its screen contracts and its `prototypes/`. This repository is one too, for its own task board tickets.
_Home_: `AGENTS.md`

**repository root**:
`git rev-parse --show-toplevel`: the working directory of every `CHECK:` unless a `CWD:` line moves it.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**subtree**:
How an upstream repository is carried inside this one (`git subtree pull --prefix … --squash`): `mmw-v2/upstream/` is `mattpocock/skills`, `mmw-v2/upstream-diagram-design/` is `cathrynlavery/diagram-design`, `mmw-v2/upstream-unlazy/` is `Leonxlnx/unlazy`. A change to a skill inside one, or to unlazy's scripts, gets a **merge-note**.
_Home_: `mmw-v2/merge-notes/README.md`

**upstream**:
The source project of a subtree. A passage no merge-note covers is upstream's text, and upstream's own `AGENTS.md`, `CLAUDE.md` and `CONTEXT.md` are kept as upstream wrote them.
_Home_: `mmw-v2/merge-notes/README.md`

**unlazy**:
The repository gate-check and gate-lint come from (`Leonxlnx/unlazy`, MIT), carried as the subtree `mmw-v2/upstream-unlazy/`. The verify-ticket skill reaches its `scripts/gate-check.mjs`, `scripts/gate-lint.mjs` and `scripts/lib/` through relative symlinks in `mmw-v2/skills/verify-ticket/scripts/gate-check/`.
_Home_: `mmw-v2/merge-notes/unlazy.md`

**source directory**:
One of the three directories a host's skill symlink points straight at: `mmw-v2/skills/`, `mmw-v2/upstream/skills/`, `mmw-v2/upstream-diagram-design/skills/`. `install.sh` treats a link as its own when it resolves inside one of them.
_Home_: `mmw-v2/install.sh`

**`~/.agents/skills`**:
The host-neutral install location `install.sh` fills on every machine, scanned by Codex, Cursor, Grok and Pi. `~/.claude/skills` is the second copy, for Claude Code.
_Home_: `docs/adr/0006-skills-install-to-neutral-dir.md`

**stale link**:
A symlink or hook registration that points back into this repository but is not on the install list, or a link left in a **retired** location. `install.sh --check` reports it as `残留` and `install.sh` removes it.
_Home_: `mmw-v2/install.sh`

**retired**:
The state of an install location `install.sh` empties and does not install into although its host still scans it (the four per-host `skills/` directories and the six subagent directories), and of a skill or subagent moved to `deprecated/`. Distinct from a frozen directory (`archive/`, `deprecated/`, `docs/research/`), which is kept as it is.
_Home_: `mmw-v2/install.sh`

**issue tracker**:
GitHub Issues for this repository (the tracker), every operation through `gh`: it holds the specs, tickets and children, their parent–child relations and blocking links, the claims and the events.
_Avoid_: board (for the tracker; the task board is the local web page)
_Home_: `docs/agents/issue-tracker.md`

**`docs/agents/`**:
The three files the `setup-matt-pocock-skills` skill seeds once — `issue-tracker.md`, `triage-labels.md`, `domain.md` — from which the upstream skills read this repository's tracker commands, labels and domain docs.
_Home_: `mmw-v2/merge-notes/setup-matt-pocock-skills.md`

**`CONTEXT.md`**:
The glossary of one bounded context, at `docs/contexts/<name>/CONTEXT.md`; the root `CONTEXT-MAP.md` lists the contexts and how they relate. `mmw-v2/upstream/CONTEXT.md` is upstream's own vocabulary and not part of it.
_Home_: `docs/agents/domain.md`

**`AGENTS.md`**:
A repository's agent instruction file, root plus nested ones, written to the fixed format of the `manage-agents-md` skill. The `CLAUDE.md` beside it holds only the line `@AGENTS.md` and any other `@` imports.
_Home_: `mmw-v2/skills/manage-agents-md/references/write.md`

### The toolbox

**skill**:
The unit the toolbox ships: one directory with a `SKILL.md`, installed when `mmw-v2/skills.txt` lists it.
_Home_: `mmw-v2/skills.txt`

**`SKILL.md`**:
A skill's entry file: its location resolves the skill's `scripts/` and `references/`, and its frontmatter `description` is the one part a host scans at start. The frontmatter switch `disable-model-invocation` makes a skill user-invoked.
_Home_: `AGENTS.md`

**`skills.txt`**:
The one list deciding which skills `install.sh` installs, one `<root>/<name>` line per skill.
_Home_: `mmw-v2/install.sh`

**`tests/run.sh`**:
The hand-run test entry point of one skill or subsystem, one directory each under `mmw-v2/tests/`. There is no aggregate runner.
_Home_: `mmw-v2/tests/AGENTS.md`

**merge-note**:
One note per changed upstream skill, and one for unlazy's scripts, in `mmw-v2/merge-notes/`: which passages this repository changed, why, and how to choose when upstream changes them again.
_Home_: `mmw-v2/merge-notes/README.md`

**downstream-note**:
One note per change in this repository that invalidates a consuming repository's screen contract, ticket `CHECK:` or `.mmw/target.json`: what changed, what goes stale and how to migrate. It is the opposite direction of a merge-note.
_Home_: `mmw-v2/downstream-notes/README.md`

**`models.json`**:
The machine-level configuration at `MMW_HOME/models.json` (default `~/.mmw/models.json`) holding the selected `runner` and one row per dispatched agent — `junior-worker`, `senior-worker`, `reviewer`, `advisor` — with its host, model and `effort`. Distinct from `hosts.json`, which records how each host starts and the first-install defaults.
_Home_: `mmw-v2/skills/dispatch/references/editing-models.md`

**`effort`**:
The `effort` field of a `models.json` row: the reasoning effort the host is started with (`high`, `xhigh`, `medium`, …). How each host takes it is in `hosts.json`.
_Home_: `mmw-v2/skills/dispatch/hosts.json`

**permissions**:
How a dispatched session is started: with every tool granted, spelled per host in `hosts.json`. There is no read-only value, so an agent that must not write is a subagent told to read only.
_Home_: `mmw-v2/skills/dispatch/hosts.json`

**`models.py`**:
`mmw-v2/skills/dispatch/scripts/models.py`, the one reader and writer of `models.json` and reader of `hosts.json`: it resolves a row's model name against the selected runner's catalog and answers which runner is selected. It runs no runner command itself.
_Home_: `mmw-v2/skills/dispatch/scripts/models.py`

**`MMW_CATALOG_MODE`**:
The variable naming the catalog `models.py` resolves a row's model name against: `paseo` for Paseo's provider catalog, `cli` (the default) for the host's own CLI. `dispatch.sh` sets it from the selected runner.
_Home_: `mmw-v2/skills/dispatch/scripts/models.py`

**`install.sh`**:
`mmw-v2/install.sh`, the one install entry: it installs the nine items its header comment lists and records its checkout in `~/.mmw/installed-root`. `install.sh --check` changes nothing and exits 1 when something is missing or stale.
_Home_: `mmw-v2/install.sh`

**`# MMW_USES:`**:
A header comment line of a runner adapter declaring one command the adapter runs; together the lines list everything the adapter asks of its binary, and `install.sh --check` compares them with that binary's help pages.
_Home_: `mmw-v2/install.sh`

**`~/.mmw/installed-root`**:
The file a full `install.sh` run writes with the path of the installed checkout's `mmw-v2/` directory. `install.sh --check` run from another checkout hands the check to that checkout's `install.sh`.
_Home_: `mmw-v2/install.sh`

**`MMW_V2_HOME`**:
A test-only variable that moves every path `install.sh` reads or writes under it and skips `launchctl` and `paseo reload`. Distinct from `MMW_HOME`, where `models.json`, the leases and the state directories live.
_Home_: `mmw-v2/install.sh`

**`--tools`**:
The repeatable flag of `verify-ticket.py`, `dispatch.sh` and `lint_screen_contract.py` naming a directory of another skill's scripts, searched before the location each script resolves from its own. `verify-ticket.py` puts the directories in force on the `PATH` of every `CHECK:`, which is why a criterion names a judge bare.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**hook**:
A program a host runs at one of its events. `install.sh` registers two in each host's own configuration: `tool-guard.py` and `turn-guard.py` of the dispatch skill.
_Home_: `mmw-v2/install.sh`

**`tool-guard.py`**:
The dispatch skill's hook that, in a session whose working directory is a ticket worktree (`issue-<n>`), refuses a command that would end a process or take the ticket out of the agent queue (`pretool`) and a call to the host's question tool (`question`).
_Home_: `mmw-v2/skills/dispatch/scripts/tool-guard.py`

**`rule-at-moment.py`**:
`mmw-v2/hooks/rule-at-moment.py`, a Claude Code hook kept in the repository and not installed by `install.sh`, which cuts a numbered rule out of `~/.claude/CLAUDE.md` and shows it to the model when that rule applies.
_Home_: `mmw-v2/hooks/rule-at-moment.py`

**`verify-ticket.py`**:
The verify-ticket skill's one script for a ticket's criteria and closing: the lint, the worker's runs, reverify, preflight, closeout, and the events around them. The skill's text calls it `<engine>`.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**`issue_tree.py`**:
The verify-ticket skill's script that reads the tree under a map, a spec or a ticket in GraphQL and refuses rather than return a list shorter than GitHub's count. `status.py` and `--lint` read a spec's batch through it.
_Home_: `docs/agents/issue-tracker.md`

**ADR**:
An architecture decision record in `docs/adr/`, named `0001-slug.md`. `docs/adr/README.md` gives its shape and is the index.
_Home_: `docs/adr/README.md`

**research file**:
The Markdown file, citing each claim's source, that the `research` skill writes where the repository already keeps such notes.
_Home_: `mmw-v2/upstream/skills/engineering/research/SKILL.md`
