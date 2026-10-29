# Toolbox

MMW seen as a repository and as an install target: the skills it ships, the upstream subtrees it copies from, where an install puts things on a machine, the prompts and hooks each host reads, and the notes and ADRs that record why. Everything here is about the toolbox as an artifact, not about a run of the pipeline through it.

Vocabulary that belongs to one skill alone, such as the design vocabulary of upstream skills like `codebase-design` or the per-language tool choices, flags and pinned versions in the `mmw-mode` skill's `references/checkers-*.md`, is defined in those files and is not repeated here. Prototype and verification concepts are defined in `docs/contexts/ui-acceptance/CONTEXT.md`; `exe-release`'s own vocabulary is defined in `docs/contexts/release/CONTEXT.md`. The code checkers' own concepts, below, are this context's.

## Language

### Roles

**host**:
The command-line agent program a session runs on, either `claude` (Claude Code) or `codex` (Codex): the `host` field of a `models.json` row. Distinct from the **runner**, which starts the session and keeps it running.

**user**:
The person who owns the products and works with the orchestrator on specs and tickets. The user is the only reader of a `ready-for-human` ticket, and `needs-triage` waits on the user's decision.

**subagent**:
An agent started inside another agent's session, holding its own context and answering back into that session; a skill sends one only at a step that names one, as the host's own general-purpose subagent, on the subagent row that step names (`default` when it names none): the row's `models.json` value for that host gives the model and effort, and `inherit`, or no saved value, keeps the sending session's. Distinct from a session a runner starts with `dispatch.sh start` or `dispatch.sh brief`, which reports outside the session that started it; a code-review axis runs as a subagent of the reviewer where the host can run one.

### Places

**MMW**:
This toolbox: the skills the user shares across hosts, repositories and machines, together with the landing pipeline and the task board. Only `mmw-v4/` is live. Earlier generations, retired material, `docs/research/` and `upstream/` are history or read-only, not sources of current facts or scripts to run.

**consuming repository**:
A repository whose real tickets run through the pipeline. This repository is one too, for one product, the task board, whose code is `mmw-v4/board/`.

**repository root**:
`git rev-parse --show-toplevel`: the working directory of every `CHECK:`.

**main worktree**:
The working tree of the repository's own clone, as against the linked worktrees `git worktree add` makes (git-worktree(1): "A repository has one main worktree … and zero or more linked worktrees"). Every worktree the pipeline makes, and this repository's **installed checkout**, sits under its `.worktrees/`. Distinct from the **repository root**, which inside a ticket worktree is that worktree's top level.

**subtree**:
How an upstream repository is carried inside this one, read-only (`git subtree pull --prefix … --squash`): `upstream/mattpocock/` is `mattpocock/skills`, `upstream/pstack/` is pstack from `cursor/plugins`, `upstream/cursor-team-kit/` is `cursor-team-kit/` from the same `cursor/plugins`, `upstream/diagram-design/` is `cathrynlavery/diagram-design`, `upstream/e2e/` is `skills/` from `tester-army/e2e`. A directory of a repository comes in as its `git subtree split`. Nothing runs from a subtree except through the `repo-root` symlink: a file a skill needs is copied into `mmw-v4/skills/`.

**upstream**:
The source project of a subtree, or of any file copied into the set. A copied file differs from its source only where a **`J` entry** in its `imports.tsv` row records the change; upstream's own `AGENTS.md`, `CLAUDE.md` and `CONTEXT.md` stay in the subtree as upstream wrote them.

**unlazy**:
The repository gate-check and gate-lint came from (`Leonxlnx/unlazy`, MIT). It is not carried as a subtree: the copy in the `verify-ticket` skill's `scripts/gate-check/` is owned here and not pulled again, and its `imports.tsv` rows name the source commit.

**`~/.agents/skills`**:
The host-neutral install location `install.sh` fills on every machine, scanned by Codex, Cursor and Grok. `~/.claude/skills` is the second copy, for Claude Code.

**stale link**:
A skill symlink, host hook registration or prompt file that this repository installed and no longer installs: a link back into `mmw-v2/` for a skill `mmw-v3/skills/` does not have, `~/.claude/rules/mmw-claude.md`, Pi's two extension files and its generated `AGENTS.md`. `install.sh --check` reports each as a `残留` line and `install.sh` removes it.

**issue tracker**:
GitHub Issues for this repository (the tracker), every operation through `gh`: it holds the specs, tickets and children, their parent–child relations and blocking edges, the claims and the events.
_Avoid_: board (for the tracker; the task board is the local web page)

**Memory record**:
One memory in Nowledge Mem, kept in the **repository Space** and found by its labels: a worker's saved fact carries `mmw-experience`, `mmw-spec-<n>`, `mmw-ticket-<n>` and, for a map task, `mmw-map-<n>`; the night's **Retro Memory** carries `mmw-retro`.

**`CONTEXT.md`**:
The glossary of one bounded context, at `docs/contexts/<name>/CONTEXT.md`; the root `CONTEXT-MAP.md` lists the contexts and how they relate. `upstream/mattpocock/GLOSSARY.md` is upstream's own vocabulary and not part of it.

**`AGENTS.md`**:
A repository's agent instruction file, root plus nested ones, which every host loads when a session starts. Claude Code loads it on its own only where no `CLAUDE.md` sits beside it; a `CLAUDE.md` that exists imports it with the line `@AGENTS.md`.

**context pointer**:
A reference in an agent's context that names material outside that context and the condition for reading it. Its wording, not the file it names, decides when an agent reaches that material.

### The toolbox

**skill**:
The unit the toolbox ships: one directory under `mmw-v3/skills/` with a `SKILL.md`, which is what makes `install.sh` install it; there is no second list. A skill says how one thing is done and what it hands back; how a whole task runs is a **playbook**.

**mode**:
The `mmw-mode` skill: the owner's way of working, which every session reads in full before any work. Its `## Non-negotiables`, `## Principles` index, `## Autonomy` and reply rules hold for every task, and a session holding a **request** goes on to its `references/handling-a-request.md`, which routes each kind of task to one playbook. A session a script starts is told to read it by its start prompt; in every repository, the host hook `session-start.py` tells a Claude Code or Codex session to read it at start, and a Claude Code session to read it again after its context is compacted.

**request**:
The owner's own words as a session's first message, naming no file to follow. A session holding a request reads the mode's `references/handling-a-request.md` in full, matches the task to a playbook, sends the sessions the playbook names and reports to the owner. Distinct from the request file a code-review reviewer reads in place of a ticket.
_Avoid_: owning a task, the owner of a task

**assignment**:
A start prompt from `dispatch.sh` or a subagent call that names the file to follow, such as `Dispatched: worker, ticket #<n>, base <commit>. Read the mmw-mode skill in full, then follow the mmw-mode skill's playbooks/work-a-ticket.md.` A session holding an assignment works by that file and reads another only where that file names it.
_Avoid_: sent agent

**playbook**:
One file under `mmw-v3/skills/mmw-mode/playbooks/` saying how one kind of task is done, start to end: what the session owns, numbered steps each ending in a **`Done when` line**, and the `**Reply:**`. It is reached only through its route line in the mode's `## Playbooks`, and named in prose by its title (`Run a night`, `Work a ticket`).

**the owner's page**:
The single visual reading and decision place for one pull request, published at the address or local path on the body's first line. Distinct from **the record**, which preserves the change's identification and evidence links.

**the record**:
The pull request body of fixed lines identifying the change and linking its ticket verdicts, landings, checks and unresolved work. The owner's explanation and decisions are on **the owner's page**.

**principle**:
A skill named `principle-<slug>` holding one judgement many tasks need. Its line in the mode's `## Principles` says when it applies and is always in context; the full text is read only then, and every step where it applies names it in bold.

**`imports.tsv`**:
`mmw-v3/imports.tsv`, one row per file copied into `mmw-v3/skills/` from anywhere else: its type, its local path, the upstream repository, the source path and commit, the mechanical changes, and its **`J` entries**. `python3 mmw-v3/check_imports.py` fails when a file has no row, a source cannot be read at its commit, or a file with no recorded edit differs from its source.

**`J` entry**:
One recorded judgement in the last column of an `imports.tsv` row, numbered `J<n>` across the whole file: one change made to the copied text, what it was and why. Every edit to a copied file adds one.

**`SKILL.md`**:
A skill's entry file: its location resolves the skill's `scripts/` and `references/`, and its frontmatter `description` is the one part a host scans at start. The frontmatter switch `disable-model-invocation` makes a skill user-invoked.

**`mmw-v3/tests/<name>/run.sh`**:
The hand-run test entry point of one skill or subsystem, one directory each under `mmw-v3/tests/`. There is no aggregate test runner.

**`disable-model-invocation` pairing**:
The rule that a skill's frontmatter `disable-model-invocation: true` (read by Claude Code) and its `agents/openai.yaml` `policy.allow_implicit_invocation: false` (read by Codex) say the same thing — the skill fires only when the user names it — and change together, on the two skills only the person starts: `teach`, `wait-what`. Touching one without the other leaves a skill user-invoked on half the hosts and model-invoked on the rest.

**`models.json`**:
The machine-level configuration at `MMW_HOME/models.json` (default `~/.mmw/models.json`) holding the selected `runner` and one row per session role `roles.json` lists (`junior-worker`, `senior-worker`, `reviewer`, `advisor`, `researcher`, `explainer`, `synthesizer`), with its host, model and `effort`; `subagents`, each subagent row's model and `effort` per host, missing or `inherit` where the sending session's apply; and `max_workers`, how many of one night's tickets may be held at once. Distinct from `hosts.json`, which records how each host starts and the first-install defaults.

**`MMW_HOME`**:
The machine's MMW directory, `~/.mmw` unless the variable names another, as `home()` in the dispatch skill's `statedir.py` resolves it. It holds `models.json` and its lock `models.lock`, the task board's `boards.json` and `board.log`, and `state/<owner>__<name>/`, one 0700 **state directory** per repository; `install.sh` also writes `installed-root` under `~/.mmw` itself. Not one byte of ticket state lives there: a ticket's state is its events.

**`effort`**:
The `effort` field of a `models.json` row: the reasoning effort the host is started with (`high`, `xhigh`, `medium`, …). How each host takes it is in `hosts.json`. Distinct from ui-acceptance's **effort** (`<effort>`), a development effort's directory name.

**permission mode**:
How a dispatched session is started: with every tool granted, spelled per host in `hosts.json`. There is no read-only value, so an agent that must not write is a subagent told to read only.

**`models.py`**:
`mmw-v3/skills/dispatch/scripts/models.py`, the one reader and writer of `models.json` and reader of `hosts.json`: it resolves a row's model name against the selected runner's catalog and answers which runner is selected. It runs no runner command itself.

**`MMW_CATALOG_MODE`**:
The variable naming the catalog `models.py` resolves a row's model name against: `paseo` for Paseo's provider catalog, `cli` (the default) for the host's own CLI. `dispatch.sh` sets it from the selected runner.

**catalog**:
The models one host offers, each with its reasoning efforts: Codex's `app-server` `model/list`, Claude's `list_models`, or Paseo's provider catalog when the selected runner is `paseo` (`MMW_CATALOG_MODE`). `catalog.json` under `MMW_HOME` holds the last successful read for each source and host, with its read time, host version, and latest failure; it is a cache, distinct from the saved choices in `models.json`. Reading every host's catalog is the scan (`models.py` `scan_host_catalogs`).

**`install.sh`**:
`mmw-v3/install.sh`, the one install entry: it installs the ten items its header comment lists, removes each **stale link**, and records its checkout's `mmw-v3/` directory in `~/.mmw/installed-root`. `install.sh --check` changes nothing and exits 1 when something is missing or stale.

**`~/.mmw/installed-root`**:
The file a full `install.sh` run writes with the path of the installed checkout's `mmw-v3/` directory. `install.sh --check` run from another checkout hands the check to that checkout's `install.sh`.

**self-hosting boundary**:
The rule that while this repository consumes its own landing pipeline, the runtime for the whole open watch is the checkout named in `~/.mmw/installed-root` when the watch opened — its skills, scripts, prompts, event vocabulary, relay and watchdog held as one frozen version until the watch closes.

**installed checkout**:
The checkout whose `mmw-v4/` directory `~/.mmw/installed-root` records, and which every host symlink points at; in this repository, the hand-made worktree `.worktrees/mmw-installed`. A watch holds it fixed for its whole duration, under the **self-hosting boundary**.

**the four promotion steps**:
The fixed order that finishes a change to this toolbox itself, taking it from `dev` to every host: commit on `dev`; fast-forward `main` to it; move the installed checkout to `main` and confirm with `install.sh --check`; push both. The third step waits while any watch is open.
_Avoid_: release (bare; risks reading as `exe-release`'s shipping of a product, a different act defined in `docs/contexts/release/CONTEXT.md`)

**`HOOKS-INSTALLED`**:
The line both install modes print once every host hook is in place.

**`缺` / `残留` / `没查`**:
The prefixes of `install.sh --check`'s lines: `缺` for an item missing, or different from what `install.sh` would write; `残留` for a **stale link**; `没查` for a check that could read nothing (no `nmem` on the machine), which does not fail the check.

**`MMW_INSTALL_HOME`**:
A test-only variable, a **test seam**, that moves every path `install.sh` and `render.py` read or write under it and skips `launchctl` and `paseo reload`. Distinct from `MMW_HOME`, where `models.json`, the leases and the state directories live.

**`--tools`**:
The repeatable override flag of `verify-ticket.py`, `dispatch.sh`, `pull_design.py` and `extract_skeleton.py` naming a directory of another skill's scripts, searched before the location each script resolves from its own path (that skill's `scripts/`, beside this one under `mmw-v3/skills/`). The test suites pass it to point at a copy. `verify-ticket.py` puts the directories in force on the `PATH` of every `CHECK:`, which is why a criterion names an oracle bare.

**host hook**:
A program a host runs at one of its own events. `install.sh` registers five handlers from four scripts in Claude Code's and Codex's own configuration: the dispatch skill's `tool-guard.py` before a tool call (`pretool`) and before the question tool (`question`), at the end of a turn (`Stop`) the dispatch skill's `turn-guard.py` and the `mmw-mode` skill's `reply-check.py`, and when a session starts (`SessionStart`) the `mmw-mode` skill's `session-start.py`; on Claude Code alone, a sixth runs `reply-check.py` before the Artifact tool (`artifact`). Distinct from a **git hook** (below) and a build hook (`docs/contexts/release/CONTEXT.md`): they share the bare word "hook" but run at different events for different reasons.

**`tool-guard.py`**:
The dispatch skill's hook that runs before a host's tool call. In a session whose working directory is a ticket worktree (`issue-<n>`), it refuses a command that would end a process outside the session's own process tree (it allows `kill [-<signal>] <pid>...` when every numeric target descends from the nearest host process, and refuses one whose ancestry it cannot read) or take the ticket out of the agent queue (`pretool`), and a call to the host's question tool (`question`). In every directory, `pretool` also refuses `gh issue comment` and `gh pr comment` with `--edit-last`, since all agents share one GitHub account and a comment is edited by its id through `gh api`; a git write from a session that is an open brief; and the removal (`git worktree remove`, `rm`) of a path that is or holds this process's working directory or is an open batch's recorded worktree.

**`verify-ticket.py`**:
The verify-ticket skill's one script for a ticket's criteria and closing: the lint, the worker's runs, reverify, preflight, closeout, and the events around them.

**`issue_tree.py`**:
The verify-ticket skill's script that reads the tree under a map, a spec or a ticket in GraphQL and refuses rather than return a list shorter than GitHub's count. `status.py` and `--lint` read a spec's batch through it.

**ADR**:
An architecture decision record in `docs/adr/`, named `0001-slug.md`. `docs/adr/README.md` gives its shape and is the index.

**research file**:
The Markdown file, citing each claim's source, that a researcher reports as its answer. Inside an effort, the unchanged file lives in the question's directory `efforts/<effort>/research/<ticket number>-<slug>/`; a research ticket's resolution comment points at the answer file.

**refusal**:
The fixed three-part shape every script refusal in this repository takes: what happened, with one checkable fact; why; what to do next. A check that can verify nothing says so rather than reading like a pass.

**shared checks**:
The four checks in `mmw-v4/tests/lib/` that every suite runs before its own tests. Distinct from the suite's tests of one skill or subsystem.

**verify-this**:
The skill that proves or disproves one claim and returns exactly one of `VERIFIED`, `NOT VERIFIED`, or `INCONCLUSIVE`. Distinct from a **feature map review**.

**feature map review**:
One owner-requested run of `maintain-verification-skill` over one product's feature map, distinct from the map itself (`docs/contexts/ui-acceptance/CONTEXT.md`) and from **verify-this**. Its outcome is **clean** when source and live coverage found nothing to ship, **changed** when proven corrections are committed and pushed, or **blocked** when coverage or safe shipping could not finish.

### Skill-set review

Vocabulary of the `writing-for-agents` skill's `SKILL-SET-RULES.md` and `WALKING-A-SKILL-SET.md` and the `mmw-mode` skill's `Authoring or modifying a skill` playbook: the rules and the review method this repository applies to its own skill set.

**skill set**:
The skills under `mmw-v4/skills/`, with the mode's playbooks and every skill's references and scripts, run by agents that each load only their own part; the unit `SKILL-SET-RULES.md` checks and the `Authoring or modifying a skill` playbook improves.

**moment**:
A point in a task that needs one coherent set of material and that a given run may reach without the others: a role arriving, one branch of a choice, a re-entry later in the same task. Inside a moment the agent follows steps.

**jump**:
A step that needs a second file, of the same skill or another, beyond the one the step already holds. Fixed by moving the material into that file; handing the whole job to another skill by name is a **hand-off**, not a jump.

**fragment**:
A reference every run of a task opens, which belongs inlined in the file that already holds the moment rather than split out on its own.

**hand-off**:
An edge A → B: one skill or agent leaves something a second reads or waits for. Broken where B needs something A never produced, or where A produces something that reaches B looking like success.

**unguided choice**:
A point where the agent must choose and the text says nothing, leaving the choice to the model's own habits; fixed by writing the criterion or making the branch explicit.

**rigid / brittle**:
The two failure modes of a flow that scripts every move instead of trusting the model with the ordinary ones: rigid, the agent follows the list even where the situation differs from it; brittle, every enumerated case must be kept in step with the text, and the case nobody listed has no guidance at all.

**duplication**:
One meaning stated in two places across the set — a script's `--help`, its refusal text, a start prompt it builds, and a template all count as places. Fixed by keeping the copy the acting agent loads at the moment it acts and deleting the rest.

**cache** (redundancy finding):
Text that restates a script's `--help`, a config file, the tracker, or a skill the agent has already loaded, rather than sending the agent to read it there.

**no-op**:
An instruction the model already follows by default, or a bare attitude ("be careful") where naming the action would do. Distinct from a **stance**, which a model does not hold by default.

**stance**:
A warning that names a temptation particular to the work and what to do instead, so it is not a **no-op**: a model would not otherwise resist that temptation on its own.

**over-specification**:
A numbered procedure for work a capable agent already does unprompted, an if-then list that mirrors a script's own branches, or an enumeration of cases one criterion would cover; fixed by replacing it with the goal and the one or two judgement calls the agent would actually get wrong.

**over-defense**:
Text or a mechanism guarding a path that does not occur, judged by whether it has ever fired and whether its case is reachable by normal input; when both answers are no, it is deleted and the residual risk is stated once.

**sediment**:
Text that is not about the task at hand now: a dated measurement, a design rationale that belongs in an ADR, or a changelog-like "no longer" / "now" sentence.

**upstream skill**:
A skill copied into `mmw-v4/skills/` from an upstream subtree, entering the set as its authors wrote it. The set changes the copy only where the change alters what the agent does, never for wording, clarity or its own voice; a newer upstream version is carried in, rewording and compression included, into every passage the set has not changed. Distinct from a local rewording, which is a finding fixed by restoring the upstream text.

**skill-set-review finding**:
An established problem in a skill's text or structure, always fixed once evidenced — there are no severity levels. Distinct from ticket-run's **review finding** and release's **release finding**.

**load finding**:
A skill-set-review finding that happens on every run of a task: material read but unused, a jump, a fragment, duplication, a cache, a no-op, over-specification.

**failure finding**:
A skill-set-review finding that an agent ends wrong or stuck, naming how that occurs where the set is actually used: the user's setup, the tracker history of past runs, or an input a script receives in normal use. A path nobody takes is not one, and text guarding such a path is an **over-defense**.

**wording finding**:
A skill-set-review finding about a sentence that misled, fixed in that sentence rather than by adding a second sentence to correct it. Distinct from a **load finding**, which is fixed in the structure.

**`Done when` line**:
The line, beginning `Done when`, on which the set's own text states a step's or a task's completion criterion. A step without one, or two statements of what "done" means for one task, is a finding.

**cognitive walkthrough**:
The review method of `WALKING-A-SKILL-SET.md`'s `# Walking a skill set` (the usability-inspection method), which the `Authoring or modifying a skill` playbook's **Prove it, once** runs: for each task an agent does with the set, read and run what that agent would, in its order, holding nothing it would not hold. **Gather the evidence** uses `### List the tasks` to map the text's entries to tasks.

**task** (skill-set-review task):
One job an agent is entered into a skill to do — consult an advisor, publish a spec, work one ticket — the unit a cognitive walkthrough walks; a skill entered mid-task is walked from its entry to its return. Distinct from ticket-run's task root.

**host and runner neutrality**:
The rule that one text serves every host and every runner: no host is the default, nothing branches on a host's or runner's name, and a difference in capability is written as the capability.

### Code checkers

**checker**:
A repository's linter, formatter or type checker: the class of tool the `Set up code checkers` playbook installs, versioned with the repository rather than the machine, so checking out a branch checks out the checkers it was written against.

**checker baseline**:
A file recording a tool's existing errors so only new ones are reported from day one, committed like the tool's own config.
_Avoid_: baseline (bare; reserved for the configuration-management sense, `docs/contexts/tickets/CONTEXT.md`)

**changed-lines filter**:
The fallback for a checker with no baseline mechanism: intersect its JSON output's line numbers with `git diff --unified=0`, after normalising both sides to the same path form.

**`scripts/check`**:
The one executable at a consuming repository's root that runs its checkers and tests in three tiers: `--staged`, a one-line hand-over to the commit-hook tool; the default tier, the dependency install, lint and type checks on the changed files, the groups the **test group map** selects; `--all`, everything runnable on the machine. It compares against `MMW_BASE_REF`, prints one `PASS|FAIL <step> <seconds>s` line per step, a `not run here:` line and a summary line, and exits 0 on a pass, 1 when the product is red, 2 when the environment cannot run it. `dispatch.sh land` runs the default tier on each merge result, and the orchestrator runs it before a closing-pass push. `dispatch.sh summary` runs `--all` at the night's end, One ticket before its pull request, and setup-mmw once when connecting a repository.
_Avoid_: checker command, repository checks (as the name of the command)

**test group map**:
The table inside `scripts/check` from changed paths to the test groups they can break, from which the default tier picks what to run. Every directory under a test root is in it or listed as excluded, and a self-check exits 1 otherwise, so a change adding a test directory, language or sub-project edits it in the same commit.

**always-run group**:
The few seconds of checks the default tier of `scripts/check` runs on every change, whatever paths changed: the ones every change can break, such as the repository's shared checks and its wiring.

**prek**:
The single-binary `pre-commit` reimplementation the `Set up code checkers` playbook wires as the commit-time git hook, reading the repository's own `.pre-commit-config.yaml`.

**git hook**:
The commit-time hook `prek` runs. Distinct from a **host hook** (above) and a build hook (`docs/contexts/release/CONTEXT.md`): the three share the bare word "hook" but run at different events for different reasons.

**`language: system`**:
The prek hook configuration telling it to run a command as-is instead of building an environment of its own for it; without it, a checker runs a second, independently versioned copy of itself inside the hook.

**`core.hooksPath` trap**:
A repository whose git config sets `core.hooksPath` never executes `.git/hooks/`, so `prek install` reports success there while the hook silently never fires; the fix is to write the hook by hand into the configured path instead.

**probe**:
A deliberately planted input with a known outcome, run through a checker or a real commit and then deleted: a defect that must fail, so a zero means clean rather than silently broken, or one clean line in a file with existing findings that must pass, so the checker baseline or changed-lines filter does not block clean edits.

### This repository's additions to upstream skills

**`visual` argument**:
`wait-what`'s own argument: `/wait-what visual`, recognised as plain text rather than through `$ARGUMENTS`, sends the skill to `VISUAL.md` instead of its default re-pitch in words.

**`VISUAL.md`**:
This repository's own reference file for `wait-what`, with no upstream source, which draws an HTML page through the `diagram-design` skill instead of re-pitching the explanation as text.

**`note`** (wizard):
The `template.sh` library function that prints one dim hint line in a stage. This repository's addition is the rule that a click path written from memory rather than from current docs gets a `note` saying so, so a later console redesign is easier to find and fix.

**self-contained page**:
`teach`'s own mechanism: a lesson embeds the component code it uses, through `<!--CSS-->`/`<!--JS-->` markers `assets/build.py` fills in, instead of linking `./assets/` by relative path, so the lesson still renders when opened outside its own directory.

**`GLOSSARY.md`** (Teaching Workspace):
`teach`'s own addition to the Teaching Workspace file list: one name per concept, used by every lesson and learning record in that workspace. Distinct from this repository's own `CONTEXT.md` glossaries.

**`repo-root` symlink**:
`diagram-design`'s own symlink, `mmw-v4/skills/diagram-design/repo-root -> ../../../upstream/diagram-design`, so a script that needs a file outside the skill directory resolves to the subtree root even when the skill is installed as a linked directory and `../../` would resolve into the host's own directory instead.

**"Hand the decision on"**:
Step 5 of the `Improve the architecture` playbook: a confirmed grilling decision goes to the `Write a spec` playbook instead of being acted on in the same session, so the deepened module or seam still passes through the ticket and acceptance pipeline.
