# Toolbox

MMW seen as a repository and as an install target: the skills it ships, the three subtrees it carries, where an install puts things on a machine, the prompts and hooks each host reads, and the notes and ADRs that record why. Everything here is about the toolbox as an artifact, not about a run of the pipeline through it.

Vocabulary that belongs to one skill alone — `design-pages`'s `pull_design.py` switches and exit codes and the style rules in `template-project-claude-md.md`; the design vocabulary of upstream skills such as `codebase-design`; `code-checkers`'s own per-language tool choices, flags and pinned versions — is defined in that skill's own files and is not repeated here. `design-pages`'s entries and the page conventions are defined in `docs/contexts/ui-acceptance/CONTEXT.md`; `exe-release`'s own vocabulary (the release manifest, the release engine, tiers, build machine, build hooks) is defined in `docs/contexts/release/CONTEXT.md`. `code-checkers`'s and `manage-agents-md`'s own concepts, below, are this context's.

## Language

### Roles

**host**:
The command-line agent program a session runs on, one of `claude`, `codex`, `grok`, `cursor`, `pi`: the `host` field of a `models.json` row. Distinct from the **runner**, which starts the session and keeps it running.
_Home_: `mmw-v2/skills/dispatch/hosts.json`

**user**:
The person who owns the products and works with the orchestrator on specs and tickets. The user is the only reader of a `ready-for-human` ticket, and `needs-triage` and `needs-info` wait on the user.
_Home_: `docs/agents/triage-labels.md`

**subagent**:
An agent started inside another agent's session, holding its own context and answering back into that session; a skill that needs one asks for the host's own general-purpose subagent, which runs on the model of the session that starts it and has no `models.json` row. Distinct from a session a runner starts with `dispatch.sh start`, which writes its result to the ticket; a code-review axis runs as a subagent of the reviewer where the host can run one.
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
GitHub Issues for this repository (the tracker), every operation through `gh`: it holds the specs, tickets and children, their parent–child relations and blocking edges, the claims and the events.
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
_Home_: `mmw-v2/skills/manage-agents-md/SKILL.md`

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

**`disable-model-invocation` pairing**:
The rule that a skill's frontmatter `disable-model-invocation: true` (read by Claude Code) and its `agents/openai.yaml` `policy.allow_implicit_invocation: false` (read by Codex) say the same thing — the skill fires only when the user names it — and change together: touching one without the other leaves a skill user-triggered on half the hosts and model-triggered on the rest.
_Home_: `mmw-v2/merge-notes/README.md`

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

**self-hosting boundary**:
The rule that while this repository consumes its own landing pipeline, the runtime for the whole open watch is the checkout named in `~/.mmw/installed-root` when the watch opened — its skills, scripts, prompts, event vocabulary, relay and watchdog held as one frozen version until the watch closes.
_Home_: `AGENTS.md`

**frozen checkout**:
The installed checkout a watch holds fixed for its whole duration, under the self-hosting boundary. Distinct from a frozen directory (`archive/`, `deprecated/`, `docs/research/`), which stays as it is indefinitely and for an unrelated reason.
_Home_: `AGENTS.md`

**the four promotion steps**:
The fixed order that finishes a change to this toolbox itself, taking it from `dev` to every host: commit on `dev`; fast-forward `main` to it; move the installed worktree to `main` and confirm with `install.sh --check`; push both. The third step waits while any watch is open.
_Avoid_: release (bare; risks reading as `exe-release`'s shipping of a product, a different act defined in `docs/contexts/release/CONTEXT.md`)
_Home_: `AGENTS.md`

**`HOOKS-INSTALLED`**:
The line both install modes print once every host hook is in place.
_Home_: `mmw-v2/install.sh`

**`没查` / `不一致`**:
`install.sh --check`'s two diagnostic words for one runner adapter's binary: "not checked" when its help page cannot be read, "inconsistent" when a flag the adapter's `# MMW_USES:` declares is gone from it.
_Home_: `mmw-v2/install.sh`

**`MMW_V2_HOME`**:
A test-only variable, `TESTING.md`'s own **test seam**, that moves every path `install.sh` reads or writes under it and skips `launchctl` and `paseo reload`. Distinct from `MMW_HOME`, where `models.json`, the leases and the state directories live.
_Home_: `mmw-v2/install.sh`

**`--tools`**:
The repeatable flag of `verify-ticket.py`, `dispatch.sh` and `pull_design.py` naming a directory of another skill's scripts, searched before the location each script resolves from its own. `verify-ticket.py` puts the directories in force on the `PATH` of every `CHECK:`, which is why a criterion names an oracle bare.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**host hook**:
A program a host runs at one of its own events. `install.sh` registers two, in each host's own configuration: `tool-guard.py` and `turn-guard.py` of the dispatch skill. Distinct from a **git hook** (below) and a build hook (`docs/contexts/release/CONTEXT.md`): the three share the bare word "hook" but run at different events for different reasons.
_Home_: `mmw-v2/install.sh`

**`tool-guard.py`**:
The dispatch skill's hook that, in a session whose working directory is a ticket worktree (`issue-<n>`), refuses a command that would end a process or take the ticket out of the agent queue (`pretool`) and a call to the host's question tool (`question`).
_Home_: `mmw-v2/skills/dispatch/scripts/tool-guard.py`

**`verify-ticket.py`**:
The verify-ticket skill's one script for a ticket's criteria and closing: the lint, the worker's runs, reverify, preflight, closeout, and the events around them.
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

**refusal**:
The fixed three-part shape every script refusal in this repository takes: what happened, with one checkable fact; why; what to do next. A check that can verify nothing says so rather than reading like a pass.
_Home_: `CODING_STANDARDS.md`; built by the `ui-acceptance` skill's `scripts/refusal.py`

**shared preflight checks**:
The three checks every skill's or subsystem's `tests/run.sh` runs before its own: `check_module_paths.py` (a script names a module file that no longer exists), `check_upstream_em_dashes.py` (an em-dash outside a fenced code block in an upstream skill's Markdown), `check_own_skill_frontmatter.py` (invalid YAML, or a key beyond `name`/`description`, on one of this repository's own skills). Distinct from `verify-ticket.py --preflight`, a worker's first step on a ticket (`docs/contexts/ticket-run/CONTEXT.md`).
_Home_: `AGENTS.md`

### Skill-set review

Vocabulary of `writing-for-agents`' `SKILL-SET-REVIEW.md` and `REVIEWING-A-SKILL-SET.md`: the rules and the review method this repository applies to its own skill set.

**moment**:
A point in a task that needs one coherent set of material and that a given run may reach without the others: a role arriving, one branch of a choice, a re-entry later in the same task. Inside a moment the agent follows steps.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**jump**:
A step that needs a second file, of the same skill or another, beyond the one the step already holds. Fixed by moving the material into that file; handing the whole job to another skill by name is a **hand-off**, not a jump.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**fragment**:
A reference every run of a task opens, which belongs inlined in the file that already holds the moment rather than split out on its own.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**hand-off**:
An edge A → B: one skill or agent leaves something a second reads or waits for. Broken where B needs something A never produced, or where A produces something that reaches B looking like success.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**unguided choice**:
A point where the agent must choose and the text says nothing, leaving the choice to the model's own habits; fixed by writing the criterion or making the branch explicit.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**rigid / brittle**:
The two failure modes of a flow that scripts every move instead of trusting the model with the ordinary ones: rigid, the agent follows the list even where the situation differs from it; brittle, every enumerated case must be kept in step with the text, and the case nobody listed has no guidance at all.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**duplication**:
One meaning stated in two places across the set — a script's `--help`, its refusal text, a start prompt it builds, and a template all count as places. Fixed by keeping the copy the acting agent loads at the moment it acts and deleting the rest.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**cache** (redundancy finding):
Text that restates a script's `--help`, a config file, the tracker, or a skill the agent has already loaded, rather than sending the agent to read it there.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**no-op**:
An instruction the model already follows by default, or a bare attitude ("be careful") where naming the action would do. Distinct from a **stance**, which a model does not hold by default.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**stance**:
A warning that names a temptation particular to the work and what to do instead, so it is not a **no-op**: a model would not otherwise resist that temptation on its own.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**over-specification**:
A numbered procedure for work a capable agent already does unprompted, an if-then list that mirrors a script's own branches, or an enumeration of cases one criterion would cover; fixed by replacing it with the goal and the one or two judgement calls the agent would actually get wrong.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**over-defense**:
Text or a mechanism guarding a path that does not occur, judged by whether it has ever fired and whether its case is reachable by normal input; when both answers are no, it is deleted and the residual risk is stated once.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**sediment**:
Text that is not about the task at hand now: a dated measurement, a design rationale that belongs in an ADR, or a changelog-like "no longer" / "now" sentence.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**upstream skill**:
A skill kept in an upstream subtree, or adapted from one, entering the set as its authors wrote it; its text changes only where the change alters what the agent does, never for wording, clarity or this set's own voice.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**skill-set-review finding**:
An established problem in a skill's text or structure, always fixed once evidenced — there are no severity levels. Distinct from ticket-run's review finding, and from the bare word "finding" `exe-release` uses for a build-failure diagnosis (`docs/contexts/release/CONTEXT.md`).
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

**load finding**:
A skill-set-review finding that happens on every run of a task: material read but unused, a jump, a fragment, duplication, a cache, a no-op, over-specification.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/REVIEWING-A-SKILL-SET.md`

**cognitive walkthrough**:
The review method of `REVIEWING-A-SKILL-SET.md` (the usability-inspection method): for each task an agent does with the set, read and run what that agent would, in its order, holding nothing it would not hold.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/REVIEWING-A-SKILL-SET.md`

**task** (skill-set-review task):
One job an agent is entered into a skill to do — consult an advisor, publish a spec, work one ticket — the unit a cognitive walkthrough walks; a skill entered mid-task is walked from its entry to its return. Distinct from ticket-run's task root.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/REVIEWING-A-SKILL-SET.md`

**host and runner neutrality**:
The rule that one text serves every host and every runner: no host is the default, nothing branches on a host's or runner's name, and a difference in capability is written as the capability. Merge-notes cross-reference it by the short label "host 中立" rather than restate it.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md`

### Code checkers

**checker**:
A repository's linter, formatter or type checker: the class of tool `code-checkers` installs, versioned with the repository rather than the machine, so checking out a branch checks out the checkers it was written against.
_Home_: `mmw-v2/skills/code-checkers/SKILL.md`

**checker baseline**:
A file recording a tool's existing errors so only new ones are reported from day one, committed like the tool's own config.
_Avoid_: baseline (bare; reserved for the configuration-management sense, `docs/contexts/tickets/CONTEXT.md`)
_Home_: `mmw-v2/skills/code-checkers/references/python.md`

**changed-lines filter**:
The fallback for a checker with no baseline mechanism: intersect its JSON output's line numbers with `git diff --unified=0`, after normalising both sides to the same path form.
_Home_: `mmw-v2/skills/code-checkers/SKILL.md`

**the one command**:
The single command a repository's `AGENTS.md` names that runs every installed checker, reporting only, with a flag for the fixes safe to apply automatically; in a consuming repository this is what `.mmw/target.json`'s `checks` runs.
_Home_: `mmw-v2/skills/code-checkers/SKILL.md`

**prek**:
The single-binary `pre-commit` reimplementation `code-checkers` wires as the commit-time git hook, reading the repository's own `.pre-commit-config.yaml`.
_Home_: `mmw-v2/skills/code-checkers/references/git-hooks.md`

**git hook**:
The commit-time hook `prek` runs. Distinct from a **host hook** (above) and a build hook (`docs/contexts/release/CONTEXT.md`): the three share the bare word "hook" but run at different events for different reasons.
_Home_: `mmw-v2/skills/code-checkers/references/git-hooks.md`

**`language: system`**:
The prek hook configuration telling it to run a command as-is instead of building an environment of its own for it; without it, a checker runs a second, independently versioned copy of itself inside the hook.
_Home_: `mmw-v2/skills/code-checkers/references/git-hooks.md`

**`core.hooksPath` trap**:
A repository whose git config sets `core.hooksPath` never executes `.git/hooks/`, so `prek install` reports success there while the hook silently never fires; the fix is to write the hook by hand into the configured path instead.
_Home_: `mmw-v2/skills/code-checkers/references/git-hooks.md`

**probe**:
Planting a defect that must fail, running the checker or a real commit, confirming the failure, then deleting it — the only way to trust that a checker reporting zero problems is clean rather than silently broken.
_Home_: `mmw-v2/skills/code-checkers/SKILL.md`

### Managing AGENTS.md

**survey list**:
The one file, `survey-list.md` in the scratch directory, that merges every group's reported facts and the user's later answers; the sole source the writing step of `manage-agents-md` reads from.
_Home_: `mmw-v2/skills/manage-agents-md/SKILL.md`

**survey entry**:
One line of the survey list, naming one fact an `AGENTS.md` might carry. Its fields, listed in its `_Home_`, decide where the fact goes and whether it is written at all.
_Home_: `mmw-v2/skills/manage-agents-md/SKILL.md`

**domain section**:
An `<important if="...">` block in an `AGENTS.md`, gathering every convention or gotcha entry that shares one `when` value, read only by tasks of that kind.
_Home_: `mmw-v2/skills/manage-agents-md/SKILL.md`

**recommended answer**:
The suggested answer `manage-agents-md` puts beside each fixed question to the user, drawn from the survey list, so the user confirms or corrects it instead of composing one from nothing. Grilling's merge-note names the same pattern for its own skill, independently.
_Home_: `mmw-v2/skills/manage-agents-md/SKILL.md`

**nested pair**:
An `AGENTS.md` and `CLAUDE.md` written for one directory that earned its own file, because an agent working there would break something it would not notice from the root file alone.
_Home_: `mmw-v2/skills/manage-agents-md/references/create.md`

**situation** (create / rewrite):
`manage-agents-md`'s two entry points, chosen by whether the repository already has an instruction file: create starts from nothing, rewrite migrates what exists.
_Home_: `mmw-v2/skills/manage-agents-md/SKILL.md`

**`destinations.md`**:
The rewrite situation's own file: one line per rule or command in an old instruction file, mapping it to where it goes in the new format, to `CODING_STANDARDS.md` or `TESTING.md`, to the user, or to removal with a reason.
_Home_: `mmw-v2/skills/manage-agents-md/references/rewrite.md`

**context pointer**:
An External References row or the subdirectory sentence in an `AGENTS.md`: its wording, not the file it names, decides whether an agent actually reaches that file.
_Home_: `mmw-v2/skills/manage-agents-md/SKILL.md`

**subdirectory sentence**:
The fixed English sentence telling an agent to read a subdirectory's `AGENTS.md` before working there, kept in English because `check.sh` finds it by its English words regardless of the file's own language.
_Home_: `mmw-v2/skills/manage-agents-md/SKILL.md`

**`check.sh`**:
`manage-agents-md`'s mechanical checker of a repository's `AGENTS.md`/`CLAUDE.md` files: line count against its limit, the `CLAUDE.md` pairing, path references, `<important>` tag balance, the subdirectory sentence, a leftover `AGENTS.override.md`.
_Home_: `mmw-v2/skills/manage-agents-md/scripts/check.sh`

**code and test rules**:
The class of survey entries describing how code or tests are written; routed to a repository's `CODING_STANDARDS.md` or `TESTING.md` instead of any `AGENTS.md`, because the reviewer's Standards and Tests axes read those two files.
_Home_: `mmw-v2/skills/manage-agents-md/SKILL.md`

### This repository's additions to other upstream skills

**`visual` tag**:
`wait-what`'s own routing flag: the bare argument `visual`, recognised as plain text rather than through `$ARGUMENTS`, sends the skill to `VISUAL.md` instead of its default text-only rerun.
_Home_: `mmw-v2/merge-notes/wait-what.md`

**`VISUAL.md`**:
This repository's own reference file for `wait-what` — not in the upstream subtree, unaffected by a subtree pull — which draws an HTML page through the `diagram-design` skill instead of rerunning the explanation as text.
_Home_: `mmw-v2/merge-notes/wait-what.md`

**stage note** (wizard):
`wizard`'s own field marking a stage's click path as written from memory rather than verified, so a later console redesign is easier to find and fix.
_Home_: `mmw-v2/merge-notes/wizard.md`

**self-contained page**:
`teach`'s own mechanism: a lesson embeds the component code it uses, through `<!--CSS-->`/`<!--JS-->` markers `assets/build.py` fills in, instead of linking `./assets/` by relative path, so the lesson still renders when opened outside its own directory.
_Home_: `mmw-v2/merge-notes/teach.md`

**`GLOSSARY.md`** (Teaching Workspace):
`teach`'s own addition to the Teaching Workspace file list: one name per concept, used by every lesson and learning record in that workspace.
_Avoid_: not to be confused with this repository's own `CONTEXT.md` glossary
_Home_: `mmw-v2/merge-notes/teach.md`

**`repo-root` symlink**:
`diagram-design`'s own symlink, `skills/diagram-design/repo-root -> ../..`, so a script resolves to the subtree root even when the skill is installed as a linked directory and `../../` would resolve into the host's own directory instead.
_Home_: `mmw-v2/merge-notes/diagram-design.md`

**"Hand the decision on"**:
`improve-codebase-architecture`'s own added final step: a confirmed grilling decision goes to the `to-spec` skill instead of being acted on in the same session, so the deepened module or seam still passes through the ticket and acceptance pipeline.
_Home_: `mmw-v2/merge-notes/improve-codebase-architecture.md`
