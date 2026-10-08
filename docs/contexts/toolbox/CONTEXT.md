# Toolbox

MMW seen as a repository and as an install target: the skills it ships, the upstream subtrees it copies from, where an install puts things on a machine, the prompts and hooks each host reads, and the notes and ADRs that record why. Everything here is about the toolbox as an artifact, not about a run of the pipeline through it.

Vocabulary that belongs to one skill alone — `design-pages`'s `pull_design.py` switches and exit codes and the style rules in `template-project-claude-md.md`; the design vocabulary of upstream skills such as `codebase-design`; the per-language tool choices, flags and pinned versions in the `mmw-mode` skill's `references/checkers-*.md` — is defined in those files and is not repeated here. `design-pages`'s entries and the page conventions are defined in `docs/contexts/ui-acceptance/CONTEXT.md`; `exe-release`'s own vocabulary (the release manifest, the release engine, tiers, build machine, build hooks) is defined in `docs/contexts/release/CONTEXT.md`. The code checkers' and `manage-agents-md`'s own concepts, below, are this context's.

## Language

### Roles

**host**:
The command-line agent program a session runs on, one of `claude`, `codex`, `grok`, `cursor`: the `host` field of a `models.json` row. Distinct from the **runner**, which starts the session and keeps it running.
_Home_: `mmw-v3/skills/dispatch/hosts.json`

**user**:
The person who owns the products and works with the orchestrator on specs and tickets. The user is the only reader of a `ready-for-human` ticket, and `needs-triage` and `needs-info` wait on the user.
_Home_: `docs/agents/triage-labels.md`

**subagent**:
An agent started inside another agent's session, holding its own context and answering back into that session; a skill that needs one asks for the host's own general-purpose subagent, which runs on the model of the session that starts it and has no `models.json` row. Distinct from a session a runner starts with `dispatch.sh start` or `dispatch.sh brief`, which reports outside the session that started it; a code-review axis runs as a subagent of the reviewer where the host can run one.
_Home_: `docs/adr/0015-no-custom-subagents.md`

### Places

**MMW**:
This toolbox (the toolbox): the skills the user shares across hosts, repositories and machines, together with the landing pipeline behind them (spec → ticket → a dispatched worker → a closed ticket) and the task board. Only `mmw-v3/` is live; `mmw-v2/` and `archive/` (earlier generations), `deprecated/` (what v2 retired) and `docs/research/code-landing-refs/` (read-only snapshots of third-party repositories) are kept for history, and the rest of `docs/research/` holds research notes a spec may cite. `mmw-v2/install.sh` is also the way back from v3 to v2 (ADR 0036).
_Home_: `AGENTS.md`

**consuming repository**:
A repository whose real tickets run through the pipeline and which holds its **product answers** in `.mmw/` and each development effort's files in `efforts/<effort>/`. This repository is one too, for its own task board tickets.
_Home_: `AGENTS.md`

**repository root**:
`git rev-parse --show-toplevel`: the working directory of every `CHECK:` unless a `CWD:` line moves it.
_Home_: `mmw-v3/skills/verify-ticket/references/ticket-format.md`

**main worktree**:
The working tree of the repository's own clone, as against the linked worktrees `git worktree add` makes (git-worktree(1): "A repository has one main worktree … and zero or more linked worktrees"). Every worktree the pipeline makes, and this repository's **installed checkout**, sits under its `.worktrees/`. Distinct from the **repository root**, which inside a ticket worktree is that worktree's top level.
_Home_: `AGENTS.md`

**subtree**:
How an upstream repository is carried inside this one, read-only (`git subtree pull --prefix … --squash`): `mmw-v3/upstream-mattpocock/` is `mattpocock/skills`, `mmw-v3/upstream-pstack/` is pstack from `cursor/plugins`, `mmw-v3/upstream-diagram-design/` is `cathrynlavery/diagram-design`. Nothing runs from a subtree: a file a skill needs is copied into `mmw-v3/skills/` and gets a row in **`imports.tsv`**.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**upstream**:
The source project of a subtree, or of any file copied into the set. A copied file differs from its source only where a **`J` entry** in its `imports.tsv` row records the change; upstream's own `AGENTS.md`, `CLAUDE.md` and `CONTEXT.md` stay in the subtree as upstream wrote them.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`, `mmw-v3/imports.tsv`

**unlazy**:
The repository gate-check and gate-lint came from (`Leonxlnx/unlazy`, MIT). It is not carried as a subtree: the copy in the `verify-ticket` skill's `scripts/gate-check/` is owned here and not pulled again, and its `imports.tsv` rows name the source commit.
_Home_: `mmw-v3/imports.tsv`, `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**`~/.agents/skills`**:
The host-neutral install location `install.sh` fills on every machine, scanned by Codex, Cursor and Grok. `~/.claude/skills` is the second copy, for Claude Code.
_Home_: `docs/adr/0006-skills-install-to-neutral-dir.md`

**stale link**:
A skill symlink, host hook registration or prompt file that this repository installed and no longer installs: a link back into `mmw-v2/` for a skill `mmw-v3/skills/` does not have, `~/.claude/rules/mmw-claude.md`, Pi's two extension files and its generated `AGENTS.md`. `install.sh --check` reports each as a `残留` line and `install.sh` removes it.
_Home_: `mmw-v3/install.sh`

**issue tracker**:
GitHub Issues for this repository (the tracker), every operation through `gh`: it holds the specs, tickets and children, their parent–child relations and blocking edges, the claims and the events.
_Avoid_: board (for the tracker; the task board is the local web page)
_Home_: `docs/agents/issue-tracker.md`

**Memory record**:
One memory in Nowledge Mem, kept in the **repository Space** and found by its labels: a worker's saved fact carries `mmw-experience`, `mmw-spec-<n>`, `mmw-ticket-<n>` and, for a map task, `mmw-map-<n>`; the night's **Retro Memory** carries `mmw-retro`.
_Home_: `mmw-v3/skills/mmw-mode/references/memory.md`, `mmw-v3/skills/retro/SKILL.md`

**`docs/agents/`**:
The three files the `setup-mmw` skill writes when it onboards a repository — `issue-tracker.md`, `triage-labels.md`, `domain.md` — from which the skills read this repository's tracker commands, labels and domain docs.
_Home_: `mmw-v3/skills/setup-mmw/SKILL.md`

**`CONTEXT.md`**:
The glossary of one bounded context, at `docs/contexts/<name>/CONTEXT.md`; the root `CONTEXT-MAP.md` lists the contexts and how they relate. `mmw-v3/upstream-mattpocock/CONTEXT.md` is upstream's own vocabulary and not part of it.
_Home_: `docs/agents/domain.md`

**`AGENTS.md`**:
A repository's agent instruction file, root plus nested ones, written to the fixed format of the `manage-agents-md` skill. The `CLAUDE.md` beside it holds only the line `@AGENTS.md` and any other `@` imports.
_Home_: `mmw-v3/skills/manage-agents-md/SKILL.md`

### The toolbox

**skill**:
The unit the toolbox ships: one directory under `mmw-v3/skills/` with a `SKILL.md`, which is what makes `install.sh` install it; there is no second list. A skill says how one thing is done and what it hands back; how a whole task runs is a **playbook**.
_Home_: `mmw-v3/skills/README.md`, `mmw-v3/install.sh`

**mode**:
The `mmw-mode` skill: the owner's way of working, which every session reads in full before any work. Its `## Non-negotiables`, `## Principles` index, `## Autonomy` and reply rules hold for every task, and its `## Playbooks` routes each kind of task to one playbook. A session a script starts is told to read it by its start prompt; in a repository with `.mmw/`, the host hook `mode-hook.py` tells a Claude Code or Codex session to read it at start.
_Home_: `mmw-v3/skills/mmw-mode/SKILL.md`

**playbook**:
One file under `mmw-v3/skills/mmw-mode/playbooks/` saying how one kind of task is done, start to end: what the session owns, numbered steps each ending in a **`Done when` line**, and the `**Reply:**`. It is reached only through its route line in the mode's `## Playbooks`, and named in prose by its title (`Run a night`, `Work a ticket`).
_Home_: `mmw-v3/skills/mmw-mode/playbooks/README.md`

**principle**:
A skill named `principle-<slug>` holding one judgement many tasks need. Its line in the mode's `## Principles` says when it applies and is always in context; the full text is read only then, and every step where it applies names it in bold.
_Home_: `mmw-v3/skills/README.md`

**`imports.tsv`**:
`mmw-v3/imports.tsv`, one row per file copied into `mmw-v3/skills/` from anywhere else: its type, its local path, the upstream repository, the source path and commit, the mechanical changes, and its **`J` entries**. `python3 mmw-v3/check_imports.py` fails when a file has no row, a source cannot be read at its commit, or a file with no recorded edit differs from its source.
_Home_: `mmw-v3/check_imports.py`

**`J` entry**:
One recorded judgement in the last column of an `imports.tsv` row, numbered `J<n>` across the whole file: one change made to the copied text, what it was and why. Every edit to a copied file adds one.
_Home_: `mmw-v3/imports.tsv`, `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**`SKILL.md`**:
A skill's entry file: its location resolves the skill's `scripts/` and `references/`, and its frontmatter `description` is the one part a host scans at start. The frontmatter switch `disable-model-invocation` makes a skill user-invoked.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**`mmw-v3/tests/<name>/run.sh`**:
The hand-run test entry point of one skill or subsystem, one directory each under `mmw-v3/tests/`. There is no aggregate test runner.
_Home_: `TESTING.md`

**`disable-model-invocation` pairing**:
The rule that a skill's frontmatter `disable-model-invocation: true` (read by Claude Code) and its `agents/openai.yaml` `policy.allow_implicit_invocation: false` (read by Codex) say the same thing — the skill fires only when the user names it — and change together, on the two skills only the person starts: `teach`, `wait-what`. Touching one without the other leaves a skill user-invoked on half the hosts and model-invoked on the rest.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**`models.json`**:
The machine-level configuration at `MMW_HOME/models.json` (default `~/.mmw/models.json`) holding the selected `runner` and one row per session role `roles.json` lists (`junior-worker`, `senior-worker`, `reviewer`, `advisor`, `researcher`, `explainer`, `synthesizer`), with its host, model and `effort`. Distinct from `hosts.json`, which records how each host starts and the first-install defaults.
_Home_: `mmw-v3/skills/dispatch/references/editing-models.md`

**`effort`**:
The `effort` field of a `models.json` row: the reasoning effort the host is started with (`high`, `xhigh`, `medium`, …). How each host takes it is in `hosts.json`. Distinct from ui-acceptance's **effort** (`<effort>`), a development effort's directory name.
_Home_: `mmw-v3/skills/dispatch/hosts.json`

**permission mode**:
How a dispatched session is started: with every tool granted, spelled per host in `hosts.json`. There is no read-only value, so an agent that must not write is a subagent told to read only.
_Home_: `mmw-v3/skills/dispatch/hosts.json`

**`models.py`**:
`mmw-v3/skills/dispatch/scripts/models.py`, the one reader and writer of `models.json` and reader of `hosts.json`: it resolves a row's model name against the selected runner's catalog and answers which runner is selected. It runs no runner command itself.
_Home_: `mmw-v3/skills/dispatch/scripts/models.py`

**`MMW_CATALOG_MODE`**:
The variable naming the catalog `models.py` resolves a row's model name against: `paseo` for Paseo's provider catalog, `cli` (the default) for the host's own CLI. `dispatch.sh` sets it from the selected runner.
_Home_: `mmw-v3/skills/dispatch/scripts/models.py`

**catalog**:
The models one host offers, each with the reasoning efforts it takes, read from the source the selected runner starts sessions through: Paseo's provider catalog for `paseo`, the host's own CLI otherwise (`MMW_CATALOG_MODE`). Reading every host's catalog is the scan (`models.py` `scan_host_catalogs`), and `models.json` accepts a row only with a model and `effort` the scan offered.
_Home_: `mmw-v3/skills/dispatch/scripts/models.py`

**`install.sh`**:
`mmw-v3/install.sh`, the one install entry: it installs the ten items its header comment lists, removes each **stale link**, and records its checkout's `mmw-v3/` directory in `~/.mmw/installed-root`. `install.sh --check` changes nothing and exits 1 when something is missing or stale.
_Home_: `mmw-v3/install.sh`

**`~/.mmw/installed-root`**:
The file a full `install.sh` run writes with the path of the installed checkout's `mmw-v3/` directory. `install.sh --check` run from another checkout hands the check to that checkout's `install.sh`.
_Home_: `mmw-v3/install.sh`

**self-hosting boundary**:
The rule that while this repository consumes its own landing pipeline, the runtime for the whole open watch is the checkout named in `~/.mmw/installed-root` when the watch opened — its skills, scripts, prompts, event vocabulary, relay and watchdog held as one frozen version until the watch closes.
_Home_: `AGENTS.md`

**installed checkout**:
The checkout whose `mmw-v3/` directory `~/.mmw/installed-root` records, and which every host symlink points at; in this repository, the hand-made worktree `.worktrees/mmw-installed`. A watch holds it fixed for its whole duration, under the **self-hosting boundary**.
_Home_: `AGENTS.md`

**the four promotion steps**:
The fixed order that finishes a change to this toolbox itself, taking it from `dev` to every host: commit on `dev`; fast-forward `main` to it; move the installed checkout to `main` and confirm with `install.sh --check`; push both. The third step waits while any watch is open.
_Avoid_: release (bare; risks reading as `exe-release`'s shipping of a product, a different act defined in `docs/contexts/release/CONTEXT.md`)
_Home_: `AGENTS.md`

**`HOOKS-INSTALLED`**:
The line both install modes print once every host hook is in place.
_Home_: `mmw-v3/install.sh`

**`缺` / `残留` / `没查`**:
The prefixes of `install.sh --check`'s lines: `缺` for an item missing, or different from what `install.sh` would write; `残留` for a **stale link**; `没查` for a check that could read nothing (no `nmem` on the machine), which does not fail the check.
_Home_: `mmw-v3/install.sh`

**`MMW_INSTALL_HOME`**:
A test-only variable, `TESTING.md`'s own **test seam**, that moves every path `install.sh` and `render.py` read or write under it and skips `launchctl` and `paseo reload`. Distinct from `MMW_HOME`, where `models.json`, the leases and the state directories live.
_Home_: `mmw-v3/install.sh`

**`--tools`**:
The repeatable override flag of `verify-ticket.py`, `dispatch.sh`, `pull_design.py` and `extract_skeleton.py` naming a directory of another skill's scripts, searched before the location each script resolves from its own path (that skill's `scripts/`, beside this one under `mmw-v3/skills/`). The test suites pass it to point at a copy. `verify-ticket.py` puts the directories in force on the `PATH` of every `CHECK:`, which is why a criterion names an oracle bare.
_Home_: `mmw-v3/skills/verify-ticket/scripts/verify-ticket.py`, `mmw-v3/skills/dispatch/scripts/dispatch.sh`

**host hook**:
A program a host runs at one of its own events. `install.sh` registers three, in each host's own configuration: `tool-guard.py` and `turn-guard.py` of the dispatch skill, and the `mmw-mode` skill's `mode-hook.py` on Claude Code's and Codex's session start. Distinct from a **git hook** (below) and a build hook (`docs/contexts/release/CONTEXT.md`): the three share the bare word "hook" but run at different events for different reasons.
_Home_: `mmw-v3/install.sh`

**`tool-guard.py`**:
The dispatch skill's hook that, in a session whose working directory is a ticket worktree (`issue-<n>`), refuses a command that would end a process or take the ticket out of the agent queue (`pretool`) and a call to the host's question tool (`question`).
_Home_: `mmw-v3/skills/dispatch/scripts/tool-guard.py`

**`verify-ticket.py`**:
The verify-ticket skill's one script for a ticket's criteria and closing: the lint, the worker's runs, reverify, preflight, closeout, and the events around them.
_Home_: `mmw-v3/skills/verify-ticket/SKILL.md`

**`issue_tree.py`**:
The verify-ticket skill's script that reads the tree under a map, a spec or a ticket in GraphQL and refuses rather than return a list shorter than GitHub's count. `status.py` and `--lint` read a spec's batch through it.
_Home_: `docs/agents/issue-tracker.md`

**ADR**:
An architecture decision record in `docs/adr/`, named `0001-slug.md`. `docs/adr/README.md` gives its shape and is the index.
_Home_: `docs/adr/README.md`

**research file**:
The Markdown file, citing each claim's source, that a researcher reports as its answer. Only a map's research ticket keeps it, as the research note under `efforts/<effort>/research/`.
_Home_: `mmw-v3/skills/research/SKILL.md`

**refusal**:
The fixed three-part shape every script refusal in this repository takes: what happened, with one checkable fact; why; what to do next. A check that can verify nothing says so rather than reading like a pass.
_Home_: `CODING_STANDARDS.md`, `mmw-v3/skills/ui-acceptance/scripts/refusal.py`

**shared checks**:
The three checks in `mmw-v3/tests/lib/` that every `mmw-v3/tests/<name>/run.sh` runs before its own: `check_module_paths.py` (a script names a module file that no longer exists), `check_wiring.py` (a route, a principle line, or a skill, file, script or `dispatch.sh` command a step names is missing), `check_skill_frontmatter.py` (invalid YAML, or a key beyond those `SKILL-SET-RULES.md` allows, on one of this repository's skills).
_Home_: `TESTING.md`, `AGENTS.md`

### Skill-set review

Vocabulary of the `writing-for-agents` skill's `SKILL-SET-RULES.md` and `WALKING-A-SKILL-SET.md` and the `mmw-mode` skill's `Review the skill set` playbook: the rules and the review method this repository applies to its own skill set.

**skill set**:
The skills under `mmw-v3/skills/`, with the mode's playbooks and every skill's references and scripts, run by agents that each load only their own part; the unit `SKILL-SET-RULES.md` checks and the `Review the skill set` playbook reviews.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**moment**:
A point in a task that needs one coherent set of material and that a given run may reach without the others: a role arriving, one branch of a choice, a re-entry later in the same task. Inside a moment the agent follows steps.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**jump**:
A step that needs a second file, of the same skill or another, beyond the one the step already holds. Fixed by moving the material into that file; handing the whole job to another skill by name is a **hand-off**, not a jump.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**fragment**:
A reference every run of a task opens, which belongs inlined in the file that already holds the moment rather than split out on its own.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**hand-off**:
An edge A → B: one skill or agent leaves something a second reads or waits for. Broken where B needs something A never produced, or where A produces something that reaches B looking like success.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**unguided choice**:
A point where the agent must choose and the text says nothing, leaving the choice to the model's own habits; fixed by writing the criterion or making the branch explicit.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**rigid / brittle**:
The two failure modes of a flow that scripts every move instead of trusting the model with the ordinary ones: rigid, the agent follows the list even where the situation differs from it; brittle, every enumerated case must be kept in step with the text, and the case nobody listed has no guidance at all.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**duplication**:
One meaning stated in two places across the set — a script's `--help`, its refusal text, a start prompt it builds, and a template all count as places. Fixed by keeping the copy the acting agent loads at the moment it acts and deleting the rest.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**cache** (redundancy finding):
Text that restates a script's `--help`, a config file, the tracker, or a skill the agent has already loaded, rather than sending the agent to read it there.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**no-op**:
An instruction the model already follows by default, or a bare attitude ("be careful") where naming the action would do. Distinct from a **stance**, which a model does not hold by default.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**stance**:
A warning that names a temptation particular to the work and what to do instead, so it is not a **no-op**: a model would not otherwise resist that temptation on its own.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**over-specification**:
A numbered procedure for work a capable agent already does unprompted, an if-then list that mirrors a script's own branches, or an enumeration of cases one criterion would cover; fixed by replacing it with the goal and the one or two judgement calls the agent would actually get wrong.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**over-defense**:
Text or a mechanism guarding a path that does not occur, judged by whether it has ever fired and whether its case is reachable by normal input; when both answers are no, it is deleted and the residual risk is stated once.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**sediment**:
Text that is not about the task at hand now: a dated measurement, a design rationale that belongs in an ADR, or a changelog-like "no longer" / "now" sentence.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**upstream skill**:
A skill copied into `mmw-v3/skills/` from an upstream subtree, entering the set as its authors wrote it; its text changes only where the change alters what the agent does, never for wording, clarity or this set's own voice.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**skill-set-review finding**:
An established problem in a skill's text or structure, always fixed once evidenced — there are no severity levels. Distinct from ticket-run's **review finding** and release's **release finding**.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/review-the-skill-set.md`

**load finding**:
A skill-set-review finding that happens on every run of a task: material read but unused, a jump, a fragment, duplication, a cache, a no-op, over-specification.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**failure finding**:
A skill-set-review finding that an agent ends wrong or stuck, naming how that occurs where the set is actually used: the user's setup, the tracker history of past runs, or an input a script receives in normal use. A path nobody takes is not one, and text guarding such a path is an **over-defense**.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/review-the-skill-set.md`

**wording finding**:
A skill-set-review finding about a sentence that misled, fixed in that sentence rather than by adding a second sentence to correct it. Distinct from a **load finding**, which is fixed in the structure.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**`Done when` line**:
The line, beginning `Done when`, on which the set's own text states a step's or a task's completion criterion. A step without one, or two statements of what "done" means for one task, is a finding.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

**cognitive walkthrough**:
The review method of `WALKING-A-SKILL-SET.md`'s `# Walking a skill set` (the usability-inspection method), which step 1 of the `Review the skill set` playbook runs: for each task an agent does with the set, read and run what that agent would, in its order, holding nothing it would not hold.
_Home_: `mmw-v3/skills/writing-for-agents/WALKING-A-SKILL-SET.md`

**task** (skill-set-review task):
One job an agent is entered into a skill to do — consult an advisor, publish a spec, work one ticket — the unit a cognitive walkthrough walks; a skill entered mid-task is walked from its entry to its return. Distinct from ticket-run's task root.
_Home_: `mmw-v3/skills/writing-for-agents/WALKING-A-SKILL-SET.md`

**host and runner neutrality**:
The rule that one text serves every host and every runner: no host is the default, nothing branches on a host's or runner's name, and a difference in capability is written as the capability.
_Home_: `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`

### Code checkers

**checker**:
A repository's linter, formatter or type checker: the class of tool the `Set up code checkers` playbook installs, versioned with the repository rather than the machine, so checking out a branch checks out the checkers it was written against.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/set-up-code-checkers.md`

**checker baseline**:
A file recording a tool's existing errors so only new ones are reported from day one, committed like the tool's own config.
_Avoid_: baseline (bare; reserved for the configuration-management sense, `docs/contexts/tickets/CONTEXT.md`)
_Home_: `mmw-v3/skills/mmw-mode/references/checkers-python.md`

**changed-lines filter**:
The fallback for a checker with no baseline mechanism: intersect its JSON output's line numbers with `git diff --unified=0`, after normalising both sides to the same path form.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/set-up-code-checkers.md`

**checker command**:
The single command a repository's `AGENTS.md` names that runs every installed checker, reporting only, with a flag for the fixes safe to apply automatically; in a consuming repository this is what `.mmw/target.json`'s `checks` runs.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/set-up-code-checkers.md`

**prek**:
The single-binary `pre-commit` reimplementation the `Set up code checkers` playbook wires as the commit-time git hook, reading the repository's own `.pre-commit-config.yaml`.
_Home_: `mmw-v3/skills/mmw-mode/references/checkers-git-hooks.md`

**git hook**:
The commit-time hook `prek` runs. Distinct from a **host hook** (above) and a build hook (`docs/contexts/release/CONTEXT.md`): the three share the bare word "hook" but run at different events for different reasons.
_Home_: `mmw-v3/skills/mmw-mode/references/checkers-git-hooks.md`

**`language: system`**:
The prek hook configuration telling it to run a command as-is instead of building an environment of its own for it; without it, a checker runs a second, independently versioned copy of itself inside the hook.
_Home_: `mmw-v3/skills/mmw-mode/references/checkers-git-hooks.md`

**`core.hooksPath` trap**:
A repository whose git config sets `core.hooksPath` never executes `.git/hooks/`, so `prek install` reports success there while the hook silently never fires; the fix is to write the hook by hand into the configured path instead.
_Home_: `mmw-v3/skills/mmw-mode/references/checkers-git-hooks.md`

**probe**:
A deliberately planted input with a known outcome, run through a checker or a real commit and then deleted: a defect that must fail, so a zero means clean rather than silently broken, or one clean line in a file with existing findings that must pass, so the checker baseline or changed-lines filter does not block clean edits. Distinct from an oracle's **negative control** (ui-acceptance), a pass built into the oracle itself.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/set-up-code-checkers.md`

### Managing AGENTS.md

**survey list**:
The one file, `survey-list.md` in the scratch directory, that merges every group's reported facts and the user's later answers; the sole source the writing step of the `Write AGENTS.md` playbook reads from.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/write-agents-md.md`

**survey entry**:
One line of the survey list, naming one fact an `AGENTS.md` might carry. Its fields, listed in its `_Home_` and in `mmw-v3/skills/mmw-mode/references/agents-md-survey.md`, decide where the fact goes and whether it is written at all; its `type` is one of `command`, `convention`, `gotcha`, `reference`, `defect` and `purpose` from the survey, or `identity` and `purpose` for the user's answers, and decides which section takes it (a `defect` goes to the report, never into a file).
_Home_: `mmw-v3/skills/mmw-mode/playbooks/write-agents-md.md`

**`<important if>` block**:
An `<important if="...">` block in an `AGENTS.md`, gathering every convention or gotcha entry that shares one `when` value, read only by tasks of that kind.
_Home_: `mmw-v3/skills/manage-agents-md/SKILL.md`

**assignment**:
The share of the repository one survey group reads, sent in that group's copy of the prompt template: a topic (toolchain, documents, history, patterns) feeding the root file, or everything under one top-level directory. Assignments are split so each fits one session.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/write-agents-md.md`

**command rule**:
The `### Writing rules` bullet that keeps a command in an `AGENTS.md` only when `--help` and the manifest's scripts do not give its meaning; on a rewrite every command of the old file passes through it.
_Home_: `mmw-v3/skills/manage-agents-md/SKILL.md`

**recommended answer**:
The suggested answer the `Write AGENTS.md` playbook puts beside each fixed question to the user, drawn from the survey list, so the user confirms or corrects it instead of composing one from nothing. The term and the pattern are upstream `grilling`'s own.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/write-agents-md.md`

**nested pair**:
An `AGENTS.md` and `CLAUDE.md` written for one directory that earned its own file, because an agent working there would break something it would not notice from the root file alone.
_Home_: `mmw-v3/skills/manage-agents-md/SKILL.md`

**situation** (create / rewrite):
The `Write AGENTS.md` playbook's two entry points, chosen by whether the repository already has an instruction file: create starts from nothing, rewrite migrates what exists.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/write-agents-md.md`

**`destinations.md`**:
The rewrite situation's own file: one line per rule or command in an old instruction file, mapping it to where it goes in the new format, to `CODING_STANDARDS.md` or `TESTING.md`, to the user, or to removal with a reason.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/write-agents-md.md`

**context pointer**:
An External References row or the subdirectory sentence in an `AGENTS.md`: its wording, not the file it names, decides whether an agent actually reaches that file.
_Home_: `mmw-v3/skills/manage-agents-md/SKILL.md`

**subdirectory sentence**:
The fixed English sentence telling an agent to read a subdirectory's `AGENTS.md` before working there, kept in English because `check.sh` finds it by its English words regardless of the file's own language.
_Home_: `mmw-v3/skills/manage-agents-md/SKILL.md`

**`check.sh`**:
`manage-agents-md`'s mechanical checker of a repository's `AGENTS.md`/`CLAUDE.md` files: line count against its limit, the `CLAUDE.md` pairing, path references, `<important>` tag balance, the subdirectory sentence, a leftover `AGENTS.override.md`.
_Home_: `mmw-v3/skills/manage-agents-md/scripts/check.sh`

**code and test rules**:
The class of survey entries describing how code or tests are written; routed to a repository's `CODING_STANDARDS.md` or `TESTING.md` instead of any `AGENTS.md`, because the reviewer's Standards and Tests axes read those two files.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/write-agents-md.md`

### This repository's additions to upstream skills

**`visual` argument**:
`wait-what`'s own argument: `/wait-what visual`, recognised as plain text rather than through `$ARGUMENTS`, sends the skill to `VISUAL.md` instead of its default re-pitch in words.
_Home_: `mmw-v3/skills/wait-what/SKILL.md`

**`VISUAL.md`**:
This repository's own reference file for `wait-what`, with no upstream source, which draws an HTML page through the `diagram-design` skill instead of re-pitching the explanation as text.
_Home_: `mmw-v3/skills/wait-what/VISUAL.md`

**`note`** (wizard):
The `template.sh` library function that prints one dim hint line in a stage. This repository's addition is the rule that a click path written from memory rather than from current docs gets a `note` saying so, so a later console redesign is easier to find and fix.
_Home_: `mmw-v3/skills/wizard/SKILL.md`

**self-contained page**:
`teach`'s own mechanism: a lesson embeds the component code it uses, through `<!--CSS-->`/`<!--JS-->` markers `assets/build.py` fills in, instead of linking `./assets/` by relative path, so the lesson still renders when opened outside its own directory.
_Home_: `mmw-v3/skills/teach/SKILL.md`

**`GLOSSARY.md`** (Teaching Workspace):
`teach`'s own addition to the Teaching Workspace file list: one name per concept, used by every lesson and learning record in that workspace. Distinct from this repository's own `CONTEXT.md` glossaries.
_Home_: `mmw-v3/skills/teach/SKILL.md`

**`repo-root` symlink**:
`diagram-design`'s own symlink, `mmw-v3/skills/diagram-design/repo-root -> ../../upstream-diagram-design`, so a script that needs a file outside the skill directory resolves to the subtree root even when the skill is installed as a linked directory and `../../` would resolve into the host's own directory instead.
_Home_: `mmw-v3/skills/diagram-design/SKILL.md`

**"Hand the decision on"**:
Step 5 of the `Improve the architecture` playbook: a confirmed grilling decision goes to the `Write a spec` playbook instead of being acted on in the same session, so the deepened module or seam still passes through the ticket and acceptance pipeline.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/improve-the-architecture.md`
