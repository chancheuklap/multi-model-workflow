# Toolbox

MMW as a shared install target, its consuming repositories and its machine configuration. Skill-set components and review vocabulary belong to Skill set; task execution belongs to Ticket run and Night.

## Language

### Roles

**host**:
The agent program a session runs on, currently Claude Code or Codex, identified by `claude` or `codex` in runtime configuration. It is distinct from the runner that starts and manages the session.

**user**:
The owner of the products and the person who makes product, scope and acceptance decisions. In MMW text, user and owner refer to this person unless a passage explicitly means a product's end user.

**subagent**:
An agent within another agent's session, with its own context and an answer returned to that parent session. It is distinct from a dispatched session managed by a runner.

### Places

**MMW**:
The owner's general project-development workflow, delivered as the MMW v4 skill set with its landing pipeline and task board. The MMW repository is one consuming project and also the project that delivers this workflow.

**consuming repository**:
A project repository developed using MMW. It can contain an ordinary product, MMW's skill set, or MMW's task board.

**repository root**:
`git rev-parse --show-toplevel`: the working directory of every `CHECK:`.

**main worktree**:
The clone's original working tree, distinct from its linked worktrees. MMW locates its pipeline worktrees under that clone's `.worktrees/`.

**subtree**:
A read-only upstream snapshot carried inside this repository. Live skills use their owned copies, except for the documented diagram-design `repo-root` link.

**upstream**:
The source project from which a skill or other material was brought into MMW. Its snapshot is comparison material; current MMW behavior is defined by the live delivered copy and its adaptation records.

**unlazy**:
The source project of the gate-check and gate-lint copies maintained by verify-ticket. Those live copies belong to MMW rather than a runtime dependency on upstream.

**`~/.agents/skills`**:
The host-neutral skill installation directory scanned by Codex, containing links to the installed checkout. Claude Code receives the same skills through `~/.claude/skills`.

**stale link**:
An MMW-owned skill link, hook registration or prompt entry absent from the current installation set. It is distinct from unrelated files installed by another tool.

**issue tracker**:
GitHub Issues for this repository (the tracker), every operation through `gh`: it holds the specs, tickets and children, their parent–child relations and blocking edges, the claims and the events.
_Avoid_: board (for the tracker; the task board is the local web page)

**Memory record**:
A reusable fact in the repository Space, identified by its task-scope and experience labels. It is distinct from authoritative ticket events and from Retrospective's tracker-based assessments.

**`CONTEXT.md`**:
The glossary of one bounded context, containing its canonical terms and definitions. MMW's root CONTEXT-MAP.md locates these files under `docs/contexts/`; an upstream glossary describes its own project.

**`AGENTS.md`**:
A repository instruction file for agents, with root and nested scopes. A root CLAUDE.md containing `@AGENTS.md` imports it for Claude Code.

**CONTEXT-MAP.md**:
The repository-root index of bounded contexts and their relationships. It supplies the entry paths discovered by session-start.py without duplicating those contexts' definitions.

**shared.md**:
The user-level prompt source at `mmw-v4/prompt/shared.md`, describing the owner and their communication needs. Installed Claude Code and Codex prompt entries link to this same source.

**session-start.py**:
The mmw-mode host hook supplying mode and glossary entry pointers at session entry and glossary reminders before user messages. It discovers both the consuming repository's glossary and the installed MMW glossary when they differ.

### The toolbox

**`mmw-v4/tests/<name>/run.sh`**:
The hand-run suite entry for one MMW subsystem under `mmw-v4/tests/`. The repository's aggregate entry is `scripts/check`.

**`models.json`**:
The machine-level saved choices for session roles, subagent rows, the selected runner and `max_workers`. Role definitions belong to roles.json and host startup conventions to hosts.json.

**`MMW_HOME`**:
The machine-local MMW configuration and coordination directory, defaulting to `~/.mmw`. It is distinct from the installed skill source and stores no authoritative ticket state.

**`effort`**:
The model reasoning-effort setting in runtime configuration. It is distinct from a development effort and its `<effort>` directory name.

**permission mode**:
The host startup permission setting used by a dispatched session. It is distinct from the read-only scope of an assignment, which is an instruction rather than a separate permission configuration.

**`models.py`**:
The dispatch module owning model configuration, host catalog reads and resolution of saved model choices. It is distinct from a runner adapter, which starts and manages sessions.

**`MMW_CATALOG_MODE`**:
The variable naming the catalog `models.py` resolves a row's model name against: `paseo` for Paseo's provider catalog, `cli` (the default) for the host's own CLI. `dispatch.sh` sets it from the selected runner.

**catalog**:
The currently available models and reasoning efforts reported by a host or selected runner. It is discovery evidence, distinct from the saved choices in models.json.

**`install.sh`**:
The installation entry at `mmw-v4/install.sh`, linking the delivered skills and shared prompt and configuring their host integration. Its `--check` entry verifies the recorded installation without taking it over.

**`~/.mmw/installed-root`**:
The machine record naming the installed checkout's `mmw-v4/` directory. An installation check from another checkout delegates to the recorded version.

**self-hosting boundary**:
The frozen-version boundary between the installed MMW runtime controlling an open watch and the MMW product being changed. The installed checkout supplies one runtime version until that watch closes.

**installed checkout**:
The checkout whose `mmw-v4/` directory `~/.mmw/installed-root` records, and which every host symlink points at; in this repository, the hand-made worktree `.worktrees/mmw-installed`. A watch holds it fixed for its whole duration, under the **self-hosting boundary**.

**the four promotion steps**:
This repository's owner-controlled sequence from a dev commit through main, the installed checkout and both origin branches. It is distinct from exe-release, which packages a consuming product.

**`HOOKS-INSTALLED`**:
The line both install modes print once every host hook is in place.

**`缺` and `残留`**:
The diagnostic family printed by installation checks for missing or stale installation items. The current script owns the exact messages and outcomes.

**`MMW_INSTALL_HOME`**:
The test-only relocation of installation destinations into an isolated home. It separates installer tests from the real host configuration and services.

**`--tools`**:
The script-location override used by MMW's cross-skill tools and isolated tests. It changes which owned script directory supplies a tool, not the authority of a running workflow.

**host hook**:
A program invoked by a host lifecycle or tool event. MMW uses tool-guard.py for restrictions, turn-guard.py for watchdog health and session-start.py for advisory mode and glossary pointers.

**`tool-guard.py`**:
The dispatch host hook enforcing tool-call restrictions for ticket workers, briefed sessions and protected worktrees. It is distinct from session-start.py's advisory glossary context.

**`verify-ticket.py`**:
The verify-ticket command entry for criterion runs, lint, publication and closeout. Ticket run defines the evidence and lifecycle concepts it records.

**`issue_tree.py`**:
The verify-ticket reader of native issue hierarchies. Its complete-tree reads support the spec batch and map relationships used across MMW.

**ADR**:
An architecture decision record in `docs/adr/`, named `0001-slug.md`. `docs/adr/README.md` gives its shape and is the index.

**refusal**:
The fixed three-part shape every script refusal in this repository takes: what happened, with one checkable fact; why; what to do next. A check that can verify nothing says so rather than reading like a pass.

**shared checks**:
The common module-path, wiring, host-neutrality and skill-frontmatter checks used by MMW's subsystem suites. They are distinct from a suite's own behavior tests.

### Code checkers

**checker**:
A repository's linter, formatter or type checker: the class of tool the `Set up code checkers` playbook installs, versioned with the repository rather than the machine, so checking out a branch checks out the checkers it was written against.

**checker baseline**:
A file recording a tool's existing errors so only new ones are reported from day one, committed like the tool's own config.
_Avoid_: baseline (bare; reserved for the configuration-management sense, `docs/contexts/tickets/CONTEXT.md`)

**changed-lines filter**:
The fallback for a checker with no baseline mechanism: intersect its JSON output's line numbers with `git diff --unified=0`, after normalising both sides to the same path form.

**`scripts/check`**:
A consuming repository's single check entry, with staged, change-selected and all runnable tiers. Its test group map relates changed paths to relevant suites; the command owns its diagnostics and result.

**test group map**:
The mapping inside a repository's scripts/check from changed paths to test groups, with explicit exclusions for test roots it does not run.

**always-run group**:
The repository check group selected for every change because its contracts span the repository. Its membership belongs to scripts/check rather than a separate glossary inventory.

**prek**:
The single-binary `pre-commit` reimplementation the `Set up code checkers` playbook wires as the commit-time git hook, reading the repository's own `.pre-commit-config.yaml`.

**git hook**:
A repository-local hook invoked by git, with prek providing the commit-time integration used by Set up code checkers. It is distinct from a host hook and a release build hook.

**`language: system`**:
The prek hook configuration telling it to run a command as-is instead of building an environment of its own for it; without it, a checker runs a second, independently versioned copy of itself inside the hook.

**`core.hooksPath` trap**:
A repository configuration where git reads hooks from a path other than `.git/hooks/`. A hook installed only in `.git/hooks/` is therefore outside the active hook location.

**probe**:
A deliberately chosen input with a known outcome that establishes whether a checker or its integration detects the promised case. It differs from an ordinary successful check of clean files.

### This repository's additions to upstream skills

**`repo-root` symlink**:
The diagram-design link to its read-only upstream resource root. It gives installed scripts a stable resource location beyond the linked skill directory.

### Configuration

**roles.json**:
The dispatch definitions of named session roles and subagent rows. It describes their jobs and startup defaults, while models.json holds this machine's selected values.

**hosts.json**:
The dispatch definitions of supported hosts and their startup conventions. It is distinct from the saved per-role selections in models.json.

**model row**:
The saved host, model and reasoning-effort selection for a dispatched session role, or a host-specific subagent row. It is distinct from the role's job definition in roles.json.

**`max_workers`**:
The configured limit on tickets held concurrently by one night. It bounds batch execution rather than defining a new worker grade or model choice.

### Repository setup and help

**`setup-mmw`**:
The [skill](../../../mmw-v4/skills/setup-mmw/SKILL.md) for connecting or checking a consuming repository against the landing pipeline's prerequisites. Machine installation remains with install.sh.

**`mmw-help`**:
The [skill](../../../mmw-v4/skills/mmw-help/SKILL.md) answering how MMW works and returning a usable prompt and its source. A help answer does not start the described work.

**`wizard`**:
The [skill](../../../mmw-v4/skills/wizard/SKILL.md) for generating a guided manual procedure for steps only a human can perform.

**Set up code checkers**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/set-up-code-checkers.md) for creating or extending a consuming repository's scripts/check and proving its checker integration.
