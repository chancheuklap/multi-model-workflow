# MMW v4

MMW v4 is a toolbox of agent skills for working on a product with coding agents. It runs on two hosts: Claude Code and Codex. Every session in every host reads one skill first, [`mmw-mode`](./skills/mmw-mode/SKILL.md). That skill matches the task to a playbook, names the skills each step runs, and holds the principles behind each decision. Every change to the product ends in one pull request that the owner can read without reading code.

The layout started from pstack, a public Cursor plugin. The skills, the playbooks and the pipeline that sends sessions to tickets are MMW's own.

New here? The [MMW v4 guide](./docs/guide/README.md) walks through a first real task, from install and prompting through verification and a night of unattended work. Unsure which skill or playbook fits? Ask [`/mmw-help`](./skills/mmw-help/SKILL.md).

## Install and go back

Installing is the owner's decision. Run every command from the root of a checkout of this repository.

```bash
bash mmw-v4/install.sh            # install v4 from this checkout
bash mmw-v4/install.sh --check    # report only: exit 0 when complete, 1 when an item is missing or left over
bash mmw-v4/install.sh --back     # go back to v3
```

`install.sh` points each host at this checkout's `mmw-v4/`:

- **Skills.** Every directory under `mmw-v4/skills/` that has a `SKILL.md` gets a symbolic link in `~/.agents/skills` and in `~/.claude/skills`. Codex reads the first directory. Claude Code reads only the second.
- **Hooks.** The `dispatch` skill's `tool-guard.py` and `turn-guard.py`, and the `mmw-mode` skill's `session-start.py` go into each host's own hook configuration. `session-start.py` supplies the mode pointer at session entry and compaction, plus glossary entry paths. Before each message, it reminds the agent to use relevant definitions already in context or read them on demand. These reminders do not judge replies or request a retry.
- **The user-level prompt.** `prompt/shared.md` reaches Claude Code as `~/.claude/CLAUDE.md`, and Codex as an `AGENTS.md` that `prompt/render.py` writes. [`prompt/README.md`](./prompt/README.md) has the details.
- **A launchd task.** `com.mmw.prompt-sync` watches `shared.md` and writes the Codex copy again after each change.
- **The task board.** The `com.mmw.board` launchd task keeps `board/supervisor.py` running, which serves one local board per repository registered in `~/.mmw/boards.json`. [`board/AGENTS.md`](./board/AGENTS.md) says how it reads GitHub and restarts onto new code.
- **Paseo and Orca settings.** Paseo gets its command link and its worktree root; install removes the Grok and Cursor providers an earlier install added. When Orca is present, it puts its worktrees under each repository's `.worktrees/`, for every repository Orca holds at that moment; `--check` reports a repository added to Orca since whose worktrees would go elsewhere, and the next install sets it.
- **`~/.mmw/models.json`.** Install writes the default file, each role's `default` in `roles.json`, when none exists. In an existing file it changes only the role rows.
- **Base tools, checked only.** Install and `--check` both check that `gh` is logged in, that `git`, `python3`, `uv` and `node` are on `PATH`, and that one runner (`paseo`, `herdr` or `orca`) is. Install installs none of them; the line for a missing one says how to get it.

Install then records this checkout's `mmw-v4/` in `~/.mmw/installed-root`. `--check` run from another checkout hands the check to the installed checkout's own `install.sh` and changes nothing.

A skill is a link, not a copy, so an edit to a `SKILL.md` reaches every host at its next call. Only the `description` in a skill's frontmatter needs a new session, because hosts read it at start.

`--back` removes what v3 cannot recognise and then runs `mmw-v3/install.sh` from the same checkout. Its exit code is v3's. The header comment of [`install.sh`](./install.sh) lists every item and what install leaves untouched.

## Two ways a change reaches the product

Each path ends in one pull request to the project branch, opened by the [Opening a PR](./skills/mmw-mode/playbooks/opening-a-pr.md) playbook. The owner reads the page the pull request's first line names, and the owner's yes merges it.

1. **A night.** A spec's published tickets run unattended. The [Run a night](./skills/mmw-mode/playbooks/run-a-night.md) playbook sends a worker to each ticket, lands each ticket that passes, and opens one pull request for the owner to read in the morning. After the owner accepts it, `dispatch.sh finish` merges it. `finish` refuses while a check is red or still running, or a review thread is open.
2. **One ticket.** Every other change, code, scripts and skill text alike. The playbook of its kind ([Bug fix](./skills/mmw-mode/playbooks/bug-fix.md), [Perf issue](./skills/mmw-mode/playbooks/perf-issue.md), [Hillclimb](./skills/mmw-mode/playbooks/hillclimb.md), [Feature](./skills/mmw-mode/playbooks/feature.md), [Refactoring](./skills/mmw-mode/playbooks/refactoring.md), [Authoring or modifying a skill](./skills/mmw-mode/playbooks/authoring-a-skill.md)) opens a ticket and its `fix-<n>` branch, writes the plan into the ticket, and hands it back to the owner. On the owner's go, the [One ticket](./skills/mmw-mode/playbooks/one-ticket.md) playbook sends a worker with `dispatch.sh send`, checks the result the way that playbook says, lands it, and opens the pull request.

Several kinds of work commit directly without a ticket. The exception list is in [`mmw-mode`'s `references/handling-a-request.md` `## Playbooks`](./skills/mmw-mode/references/handling-a-request.md#playbooks). The [`exe-release`](./skills/exe-release/SKILL.md) skill packages the current branch as it stands, and a fix its build needs is committed there by the session driving the release and listed in its report.

The full list of playbooks is the `## Playbooks` section of [`mmw-mode`'s `references/handling-a-request.md`](./skills/mmw-mode/references/handling-a-request.md). [`docs/retired-playbooks/README.md`](./docs/retired-playbooks/README.md) lists the retired playbooks and what replaced each one.

## Why there are planning playbooks

pstack has none. Its author holds that the best spec is code. MMW departs from that, because its owner does not read code. A spec and its tickets are what the owner can check and accept before agents build from them unattended.

[Grill with docs](./skills/mmw-mode/playbooks/grill-with-docs.md), or a wayfinder map ([Chart the map](./skills/mmw-mode/playbooks/chart-the-map.md), then [Work through the map](./skills/mmw-mode/playbooks/work-through-the-map.md)), settles the decisions. [To spec](./skills/mmw-mode/playbooks/to-spec.md) records them and decides nothing new. [To tickets](./skills/mmw-mode/playbooks/to-tickets.md) cuts them into tickets with acceptance criteria. Design questions are still settled in code first. The [`prototype`](./skills/prototype/SKILL.md) skill answers questions about logic, UI, implementation, and code shape. Its [sketch branch](./skills/prototype/SKETCH.md) settles a shape that reaches beyond one ticket.

## Skills

`mmw-mode` runs most of these when a step names them. You can also name one in a prompt, such as `/how do we cancel runs?`. The 35 principle skills are in the next section.

| Skill | Use it to |
| --- | --- |
| [`mmw-mode`](./skills/mmw-mode/SKILL.md) | Pick the playbook for a task, run the skills its steps name, and apply the principles. Every session reads it first. |
| [`mmw-help`](./skills/mmw-help/SKILL.md) | Ask which skill, playbook or principle fits. It answers and hands you a prompt to send, without starting the work. |
| [`how`](./skills/how/SKILL.md) | Get a walkthrough of how a subsystem works, at the level of a senior engineer onboarding onto it. |
| [`why`](./skills/why/SKILL.md) | Find out why code is shaped the way it is, from its history and other evidence, with stated confidence. |
| [`teach`](./skills/teach/SKILL.md) | Understand a change or subsystem. It runs `how` and `why` and builds one plain explanation, diagram by diagram. |
| [`research`](./skills/research/SKILL.md) | Investigate a question against primary sources and get the findings as one cited Markdown file. |
| [`blast-radius`](./skills/blast-radius/SKILL.md) | Find what a small change could break elsewhere, with the facts its safety depends on proven by running code. |
| [`codebase-design`](./skills/codebase-design/SKILL.md) | Use the shared vocabulary for deep modules: module, interface, depth, seam, adapter, leverage, locality. |
| [`arena`](./skills/arena/SKILL.md) | Compare designs of the same task from different angles and graft the best parts onto the selected base. |
| [`swarm`](./skills/swarm/SKILL.md) | Run several parallel workers on separate slices or on the same brief, then get one aggregated report. |
| [`prototype`](./skills/prototype/SKILL.md) | Build code that answers one logic, UI, implementation or code-shape question, kept under `efforts/<effort>/prototypes/`, with non-UI verdicts on the ticket. |
| [`wizard`](./skills/wizard/SKILL.md) | Get a bash script that walks a person, stage by stage, through steps only they can take, such as setting up a cloud account or credentials. |
| [`grilling`](./skills/grilling/SKILL.md) | Have a plan or idea stress-tested in rounds of numbered questions, each with a recommended answer. |
| [`domain-modeling`](./skills/domain-modeling/SKILL.md) | Settle the project's terms and record decisions in the glossary and the ADRs. |
| [`advisor`](./skills/advisor/SKILL.md) | Get a second opinion on one decision from a session on a stronger model. |
| [`sharpen`](./skills/sharpen/SKILL.md) | Examine the expert approach, your real goal, constraints and an outside check before work starts, with the conclusions returned for your decision. |
| [`tdd`](./skills/tdd/SKILL.md) | Write the failing test first, then the code, with tests only at agreed seams. |
| [`code-review`](./skills/code-review/SKILL.md) | Review a finished diff on four axes: Standards, Spec, Tests and Correctness. |
| [`no-comments`](./skills/no-comments/SKILL.md) | Strip comments from a diff before review, and fix or encode what the accepted findings name. |
| [`unslop`](./skills/unslop/SKILL.md) | Remove AI writing patterns from any text. |
| [`technical-writing`](./skills/technical-writing/SKILL.md) | Write docs, readmes, PR descriptions and commit messages to a layered standard. |
| [`writing-for-agents`](./skills/writing-for-agents/SKILL.md) | Write a skill, an `AGENTS.md` or any document an agent reads. |
| [`wait-what`](./skills/wait-what/SKILL.md) | Re-pitch the last message in words or with `visual` as one HTML page; catch up with `ketchup`; align on your goal with `in-your-own-words`, then wait for your confirmation. |
| [`diagram-design`](./skills/diagram-design/SKILL.md) | Draw a diagram or an HTML page that explains something to a person, in one house style; the skill that makes the page says what goes on it. |
| [`exe-release`](./skills/exe-release/SKILL.md) | Build an install package from the code on the current branch. |
| [`typescript-best-practices`](./skills/typescript-best-practices/SKILL.md) | Apply type-system discipline when reading or editing TypeScript. |
| [`control-cli`](./skills/control-cli/SKILL.md) | Drive, inspect and profile a CLI or terminal UI through a repeatable local harness. |
| [`control-ui`](./skills/control-ui/SKILL.md) | Drive and inspect a web, IDE or Electron UI through a local browser harness. |
| [`create-verification-skill`](./skills/create-verification-skill/SKILL.md) | When you name it, generate an e2e-based `verify-<product>` in the product repository's `.agents/skills/verify-<product>/` and tests in `tests/e2e/<product>/`, prove them once, and commit directly. |
| [`maintain-verification-skill`](./skills/maintain-verification-skill/SKILL.md) | When you request it, align a `verify-<product>` feature map and e2e tests with the product and commit proven corrections directly. |
| [`benchmark-checklist`](./skills/benchmark-checklist/SKILL.md) | Vet a measured speedup or regression before you report it or act on it. |
| [`dispatch`](./skills/dispatch/SKILL.md) | Send a session to a ticket or a brief, run a night as its orchestrator, run one ticket outside a night, change a role's host, model, effort or runner, or open the local task board. |
| [`setup-mmw`](./skills/setup-mmw/SKILL.md) | Set a repository up for the landing pipeline, or check one already set up: its labels, ignored directories, checks, and a `CLAUDE.md` that imports `AGENTS.md` when it has none. |
| [`verify-ticket`](./skills/verify-ticket/SKILL.md) | Run a ticket's acceptance criteria and close the ticket when they pass. |
| [`resolving-merge-conflicts`](./skills/resolving-merge-conflicts/SKILL.md) | Finish a merge or rebase that has conflicts, or a clean merge that turns the checks red. |
| [`register-problem`](./skills/register-problem/SKILL.md) | Register an evidenced problem that cannot be fixed in the current work, preserving repeated occurrences. |
| [`retro`](./skills/retro/SKILL.md) | Gather and sort one run's registrations and signals into proposals for the owner. |
| [`correct`](./skills/correct/SKILL.md) | Stop a repeated agent mistake by changing the repository: architecture first, then types and checks, then tests, then docs. |

## Principles

Each principle is a short skill with one rule. The `## Principles` section of `mmw-mode` indexes all 35 and says when each applies. A session reads a principle's own `SKILL.md` before it applies the principle, and its reply names each principle that changed a decision. The rule below is a summary of that index entry.

| Group | Principle | Rule |
| --- | --- | --- |
| Core | [`principle-laziness-protocol`](./skills/principle-laziness-protocol/SKILL.md) | Bias to deletion and the smallest change that solves the problem. |
| Core | [`principle-foundational-thinking`](./skills/principle-foundational-thinking/SKILL.md) | Settle the core types and data structures, the order of scaffold and feature, and what concurrent actors share, before writing logic. |
| Core | [`principle-redesign-from-first-principles`](./skills/principle-redesign-from-first-principles/SKILL.md) | Redesign as if a new requirement had been part of the design from day one. |
| Core | [`principle-attack-the-premise`](./skills/principle-attack-the-premise/SKILL.md) | When two fixes that share one premise fail the same check, write the premise down and test it directly before writing a third. |
| Core | [`principle-subtract-before-you-add`](./skills/principle-subtract-before-you-add/SKILL.md) | Remove dead weight first, then build on the simpler base. |
| Core | [`principle-minimize-reader-load`](./skills/principle-minimize-reader-load/SKILL.md) | Count layers and hidden state, collapse one-caller wrappers, and shrink mutable scope. |
| Core | [`principle-outcome-oriented-execution`](./skills/principle-outcome-oriented-execution/SKILL.md) | In a planned rewrite or migration, converge on the target design and keep no throwaway compatibility states. |
| Core | [`principle-experience-first`](./skills/principle-experience-first/SKILL.md) | Choose what serves the user over what is convenient to build. |
| Core | [`principle-exhaust-the-design-space`](./skills/principle-exhaust-the-design-space/SKILL.md) | For a decision with no precedent, build two or three competing prototypes and compare them before committing. |
| Core | [`principle-first-principles-thinking`](./skills/principle-first-principles-thinking/SKILL.md) | Challenge the premise, reduce the requirements, keep only constraints with independent support, and rebuild the simplest solution. |
| Core | [`principle-start-from-what-exists`](./skills/principle-start-from-what-exists/SKILL.md) | Search this repository, then GitHub and the package registries, before building, and decide to use, extend or build. |
| Core | [`principle-read-before-you-conclude`](./skills/principle-read-before-you-conclude/SKILL.md) | Read a file before you change it or reason about it, and label a conclusion that rests on an unread part as inferred. |
| Core | [`principle-build-the-lever`](./skills/principle-build-the-lever/SKILL.md) | Build the tool that does or proves the work, such as a script or a codemod, instead of working by hand. |
| Architecture | [`principle-model-the-domain`](./skills/principle-model-the-domain/SKILL.md) | Encode the domain in a structure, such as a state machine or a table, instead of scattered conditionals. |
| Architecture | [`principle-boundary-discipline`](./skills/principle-boundary-discipline/SKILL.md) | Put guards at system boundaries, trust internal types, and keep business logic pure. |
| Architecture | [`principle-type-system-discipline`](./skills/principle-type-system-discipline/SKILL.md) | Make illegal states unrepresentable, brand primitives, and parse external data at boundaries. |
| Architecture | [`principle-make-operations-idempotent`](./skills/principle-make-operations-idempotent/SKILL.md) | Make a command or a loop reach the same end state after crashes and retries. |
| Architecture | [`principle-migrate-callers-then-delete-legacy-apis`](./skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | Migrate every caller and delete the old API in one wave. |
| Architecture | [`principle-separate-before-serializing-shared-state`](./skills/principle-separate-before-serializing-shared-state/SKILL.md) | When concurrent actors might write the same thing, remove the sharing first. |
| Verification | [`principle-prove-it-works`](./skills/principle-prove-it-works/SKILL.md) | Before declaring done, check the real artifact, not a proxy or "it compiles". |
| Verification | [`principle-fix-root-causes`](./skills/principle-fix-root-causes/SKILL.md) | Trace each symptom back to the first place the system went wrong and fix it there; a guard is a fix only when the state it handles is legitimate. |
| Verification | [`principle-sequence-verifiable-units`](./skills/principle-sequence-verifiable-units/SKILL.md) | Break multi-step work into small units that each end in a check, and verify each before the next. |
| Verification | [`principle-test-behavior-not-implementation`](./skills/principle-test-behavior-not-implementation/SKILL.md) | Assert what the code's users can observe, so the test fails when that behavior breaks and keeps passing when only the internals change. |
| Verification | [`principle-baseline-is-the-contract`](./skills/principle-baseline-is-the-contract/SKILL.md) | Copy a settled answer, prototype or signed-off page exactly, and raise a gap to whoever owns it. |
| Verification | [`principle-run-the-smallest-test-set`](./skills/principle-run-the-smallest-test-set/SKILL.md) | Run the smallest test set that proves the change, and a full suite only for a gate or a named risk. |
| Verification | [`principle-explain-the-number`](./skills/principle-explain-the-number/SKILL.md) | Before you trust a measured number, find what limits it and rule out that it measured something else. |
| Verification | [`principle-fail-loudly`](./skills/principle-fail-loudly/SKILL.md) | A failure names what failed, what was expected and where to change it; nothing passes silently. |
| Delegation | [`principle-guard-the-context-window`](./skills/principle-guard-the-context-window/SKILL.md) | Send bulk work to subagents and keep summaries in the main thread. |
| Delegation | [`principle-never-block-on-the-human`](./skills/principle-never-block-on-the-human/SKILL.md) | Do reversible work and show the result, and ask only about a decision that belongs to the owner. |
| Delegation | [`principle-progress-is-what-the-record-says`](./skills/principle-progress-is-what-the-record-says/SKILL.md) | Where work stands is what the ticket, branch, map or resume note says, not what the session remembers. |
| Writing | [`principle-write-for-where-it-is-read`](./skills/principle-write-for-where-it-is-read/SKILL.md) | Before writing, name who reads the text, what they are doing then, and what they can see. |
| Writing | [`principle-everything-at-hand`](./skills/principle-everything-at-hand/SKILL.md) | Put everything needed to understand each place on a page where the reader looks at that place. |
| Writing | [`principle-anchor-every-reference`](./skills/principle-anchor-every-reference/SKILL.md) | Name a file, section, rule or event by its path and its heading, identifier or rule number, the same way each time. |
| Writing | [`principle-files-describe-the-present`](./skills/principle-files-describe-the-present/SKILL.md) | Write only what is true now. What changed and why goes in the commit message and the reply. |
| Meta | [`principle-encode-lessons-in-structure`](./skills/principle-encode-lessons-in-structure/SKILL.md) | When you write the same instruction a second time, encode it as a lint, a flag, a runtime check or a script. |

## Models

The `dispatch` skill sends sessions in seven roles, listed in [`roles.json`](./skills/dispatch/roles.json): `junior-worker`, `senior-worker`, `reviewer`, `researcher`, `candidate`, `retro-analyst` and `advisor`. Each role is one row of `~/.mmw/models.json`, which names its host, its model and its reasoning effort. The same file names the runner that starts the sessions. A role's `default` in `roles.json` is the row install writes for it on a machine whose file lacks one.

Change it only with `models.py config`. A change takes effect at the next session start, with no restart and no reinstall.

```bash
python3 mmw-v4/skills/dispatch/scripts/models.py config show
python3 mmw-v4/skills/dispatch/scripts/models.py config set <role> <host> <model> <effort>
python3 mmw-v4/skills/dispatch/scripts/models.py config runner <orca|herdr|paseo|auto>
```

[`editing-models.md`](./skills/dispatch/references/editing-models.md) explains each command and the limits of each host.

## License

MIT
