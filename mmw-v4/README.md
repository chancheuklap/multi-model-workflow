# MMW v4

MMW v4 is a toolbox of agent skills for working on a product with coding agents. It runs on four hosts: Claude Code, Codex, Cursor and Grok. Every session in every host reads one skill first, [`mmw-mode`](./skills/mmw-mode/SKILL.md). That skill matches the task to a playbook, names the skills each step runs, and holds the principles behind each decision. Every change to the product ends in one pull request that the owner can read without reading code.

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

- **Skills.** Every directory under `mmw-v4/skills/` that has a `SKILL.md` gets a symbolic link in `~/.agents/skills` and in `~/.claude/skills`. Codex, Cursor and Grok read the first directory. Claude Code reads only the second.
- **Hooks.** The `dispatch` skill's `tool-guard.py` and `turn-guard.py` go into each host's own hook configuration.
- **The user-level prompt.** `prompt/shared.md` reaches Claude Code as `~/.claude/CLAUDE.md`, and Codex and Grok as an `AGENTS.md` that `prompt/render.py` writes. Cursor's user-level prompt is pasted into the app by hand. [`prompt/README.md`](./prompt/README.md) has the details.
- **A launchd task.** `com.mmw.prompt-sync` watches `shared.md` and writes the Codex and Grok copies again after each change.
- **Paseo and Orca settings.** Paseo gets its command link, two providers and its worktree root. When Orca is present, it puts its worktrees under each repository's `.worktrees/`.
- **`~/.mmw/models.json`.** Install writes the default file when none exists. In an existing file it changes only the role rows.

Install then records this checkout's `mmw-v4/` in `~/.mmw/installed-root`. `--check` run from another checkout hands the check to the installed checkout's own `install.sh` and changes nothing.

A skill is a link, not a copy, so an edit to a `SKILL.md` reaches every host at its next call. Only the `description` in a skill's frontmatter needs a new session, because hosts read it at start.

`--back` removes what v3 cannot recognise and then runs `mmw-v3/install.sh` from the same checkout. Its exit code is v3's. The header comment of [`install.sh`](./install.sh) lists every item and what install leaves untouched.

## Three ways a change reaches the product

Each path ends in one pull request to the project branch. The owner reads its top half, and the owner's yes merges it.

1. **A night.** A spec's published tickets run unattended. The [Run a night](./skills/mmw-mode/playbooks/run-a-night.md) playbook sends a worker to each ticket, lands each ticket that passes, and opens one pull request for the owner to read in the morning. After the owner accepts it, `dispatch.sh finish` merges it. `finish` refuses while a check is red or still running, or a review thread is open.
2. **A day ticket.** [Bug fix](./skills/mmw-mode/playbooks/bug-fix.md), [Perf issue](./skills/mmw-mode/playbooks/perf-issue.md) and [Hillclimb](./skills/mmw-mode/playbooks/hillclimb.md) diagnose the problem and write one ticket. Run a night's **One ticket** section then cuts a `fix-<n>` branch, sends a worker with `dispatch.sh send`, checks the result on the original reproduction, lands it, and opens the pull request.
3. **A day change with no ticket.** In [Feature](./skills/mmw-mode/playbooks/feature.md), [Refactoring](./skills/mmw-mode/playbooks/refactoring.md) and [Visual parity](./skills/mmw-mode/playbooks/visual-parity.md), the session writes the change itself. [Shared closing](./skills/mmw-mode/playbooks/shared-closing.md) then proves it on the product, cleans the comments, has it reviewed on the four axes of `code-review`, commits it, merges the latest project branch, and opens the pull request.

The full list of playbooks is the `## Playbooks` section of [`mmw-mode`](./skills/mmw-mode/SKILL.md). The Babysit, Shipping, Opening a PR, Autonomous run, Orchestrate, Autopilot-full, Autopilot-stack and Multi-phase plan playbooks are retired. [`docs/retired-playbooks/README.md`](./docs/retired-playbooks/README.md) says what replaced each one.

## Why there are planning playbooks

pstack has none. Its author holds that the best spec is code. MMW departs from that, because its owner does not read code. A spec and its tickets are what the owner can check and accept before agents build from them unattended.

[Grill with docs](./skills/mmw-mode/playbooks/grill-with-docs.md), or a wayfinder map ([Chart the map](./skills/mmw-mode/playbooks/chart-the-map.md), then [Work through the map](./skills/mmw-mode/playbooks/work-through-the-map.md)), settles the decisions. [To spec](./skills/mmw-mode/playbooks/to-spec.md) records them and decides nothing new. [To tickets](./skills/mmw-mode/playbooks/to-tickets.md) cuts them into tickets with acceptance criteria. Design questions are still settled in code first. A prototype answers a question about behaviour, and [`architect`](./skills/architect/SKILL.md) sketches the shape of the code.

## Skills

`mmw-mode` runs most of these when a step names them. You can also name one in a prompt, such as `/how do we cancel runs?`. The 33 principle skills are in the next section.

| Skill | Use it to |
| --- | --- |
| [`mmw-mode`](./skills/mmw-mode/SKILL.md) | Pick the playbook for a task, run the skills its steps name, and apply the principles. Every session reads it first. |
| [`mmw-help`](./skills/mmw-help/SKILL.md) | Ask which skill, playbook or principle fits. It answers and hands you a prompt to send, without starting the work. |
| [`how`](./skills/how/SKILL.md) | Get a walkthrough of how a subsystem works, at the level of a senior engineer onboarding onto it. |
| [`why`](./skills/why/SKILL.md) | Find out why code is shaped the way it is, from its history and other evidence, with stated confidence. |
| [`teach`](./skills/teach/SKILL.md) | Understand a change or subsystem. It runs `how` and `why` and builds one plain explanation, diagram by diagram. |
| [`recall`](./skills/recall/SKILL.md) | Rebuild your recent working context on a topic from chat history and the shared record, as a short current-state brief. |
| [`research`](./skills/research/SKILL.md) | Investigate a question against primary sources and get the findings as one cited Markdown file. |
| [`blast-radius`](./skills/blast-radius/SKILL.md) | Find what a small change could break elsewhere, with the facts its safety depends on proven by running code. |
| [`architect`](./skills/architect/SKILL.md) | Settle types, signatures and module shape from several design angles before implementing. It writes no implementation. |
| [`codebase-design`](./skills/codebase-design/SKILL.md) | Use the shared vocabulary for deep modules: module, interface, depth, seam, adapter, leverage, locality. |
| [`arena`](./skills/arena/SKILL.md) | Run several designs of the same task from different angles, pick the strongest as the base, and graft in the best parts of the others. |
| [`swarm`](./skills/swarm/SKILL.md) | Run several parallel workers on separate slices or on the same brief, then get one aggregated report. |
| [`prototype`](./skills/prototype/SKILL.md) | Build code that answers one design or behaviour question, kept in the repository under `efforts/<effort>/prototypes/`. |
| [`grilling`](./skills/grilling/SKILL.md) | Have a plan or idea stress-tested in rounds of numbered questions, each with a recommended answer. |
| [`domain-modeling`](./skills/domain-modeling/SKILL.md) | Settle the project's terms and record decisions in the glossary and the ADRs. |
| [`advisor`](./skills/advisor/SKILL.md) | Get a second opinion on one decision from a session on a stronger model. |
| [`figure-it-out`](./skills/figure-it-out/SKILL.md) | Design a rigorous, auditable playbook when no bundled playbook fits the task. |
| [`tdd`](./skills/tdd/SKILL.md) | Write the failing test first, then the code, with tests only at agreed seams. |
| [`code-review`](./skills/code-review/SKILL.md) | Review a finished diff on four axes: Standards, Spec, Tests and Correctness. |
| [`no-comments`](./skills/no-comments/SKILL.md) | Strip comments from a diff before review, and fix or encode what the accepted findings name. |
| [`unslop`](./skills/unslop/SKILL.md) | Remove AI writing patterns from any text. |
| [`technical-writing`](./skills/technical-writing/SKILL.md) | Write docs, readmes, PR descriptions and commit messages to a layered standard. |
| [`writing-for-agents`](./skills/writing-for-agents/SKILL.md) | Write a skill, an `AGENTS.md` or any document an agent reads. |
| [`bro`](./skills/bro/SKILL.md) | Have the last message restated in plain language, without jargon. |
| [`typescript-best-practices`](./skills/typescript-best-practices/SKILL.md) | Apply type-system discipline when reading or editing TypeScript. |
| [`control-cli`](./skills/control-cli/SKILL.md) | Drive, inspect and profile a CLI or terminal UI through a repeatable local harness. |
| [`control-ui`](./skills/control-ui/SKILL.md) | Drive and inspect a web, IDE or Electron UI through a local browser harness. |
| [`create-verification-skill`](./skills/create-verification-skill/SKILL.md) | Generate a project-local skill that launches the app, drives a feature the way a user does, and captures evidence. |
| [`maintain-verification-skill`](./skills/maintain-verification-skill/SKILL.md) | Bring a verification skill's feature map back in line with the app, in at most one pull request. |
| [`benchmark-checklist`](./skills/benchmark-checklist/SKILL.md) | Vet a measured speedup or regression before you report it or act on it. |
| [`show-me-your-work`](./skills/show-me-your-work/SKILL.md) | Keep a decision log as a TSV file, one row per decision, for review after you step away. |
| [`dispatch`](./skills/dispatch/SKILL.md) | Send a session to a ticket or a brief, run a night as its orchestrator, run one ticket outside a night, or change a role's host, model, effort or runner. |
| [`verify-ticket`](./skills/verify-ticket/SKILL.md) | Run a ticket's acceptance criteria and close the ticket when they pass. |
| [`resolving-merge-conflicts`](./skills/resolving-merge-conflicts/SKILL.md) | Finish a merge or rebase that has conflicts, or a clean merge that turns the checks red. |
| [`reflect`](./skills/reflect/SKILL.md) | Capture what a long task taught as an edit to a skill. |
| [`correct`](./skills/correct/SKILL.md) | Stop a repeated agent mistake by changing the repository: architecture first, then types and checks, then tests, then docs. |
| [`automate-me`](./skills/automate-me/SKILL.md) | Draft your own `-mode` skill from how you have worked. |

## Principles

Each principle is a short skill with one rule. The `## Principles` section of `mmw-mode` indexes all 33 and says when each applies. A session reads a principle's own `SKILL.md` before it applies the principle, and its reply names each principle that changed a decision. The rule below is a summary of that index entry.

| Group | Principle | Rule |
| --- | --- | --- |
| Core | [Laziness Protocol](./skills/principle-laziness-protocol/SKILL.md) | Bias to deletion and the smallest change that solves the problem. |
| Core | [Foundational Thinking](./skills/principle-foundational-thinking/SKILL.md) | Settle the core types and data structures, the order of scaffold and feature, and what concurrent actors share, before writing logic. |
| Core | [Redesign From First Principles](./skills/principle-redesign-from-first-principles/SKILL.md) | Redesign as if a new requirement had been part of the design from day one. |
| Core | [Attack the Premise](./skills/principle-attack-the-premise/SKILL.md) | When two fixes that share one premise fail the same check, question the premise instead of writing a third. |
| Core | [Subtract Before You Add](./skills/principle-subtract-before-you-add/SKILL.md) | Remove dead weight first, then build on the simpler base. |
| Core | [Minimize Reader Load](./skills/principle-minimize-reader-load/SKILL.md) | Count layers and hidden state, collapse one-caller wrappers, and shrink mutable scope. |
| Core | [Outcome-Oriented Execution](./skills/principle-outcome-oriented-execution/SKILL.md) | In a planned rewrite or migration, converge on the target design and keep no throwaway compatibility states. |
| Core | [Experience First](./skills/principle-experience-first/SKILL.md) | Choose what serves the user over what is convenient to build. |
| Core | [Exhaust the Design Space](./skills/principle-exhaust-the-design-space/SKILL.md) | For a decision with no precedent, build two or three competing prototypes and compare them before committing. |
| Core | [First-Principles Thinking](./skills/principle-first-principles-thinking/SKILL.md) | Challenge the premise, reduce the requirements, keep only constraints with independent support, and rebuild the simplest solution. |
| Core | [Start From What Exists](./skills/principle-start-from-what-exists/SKILL.md) | Search this repository, then GitHub and the package registries, before building, and decide to use, extend or build. |
| Core | [Read Before You Conclude](./skills/principle-read-before-you-conclude/SKILL.md) | Read a file before you change it or reason about it, and label a conclusion that rests on an unread part as inferred. |
| Core | [Build the Lever](./skills/principle-build-the-lever/SKILL.md) | Build the tool that does or proves the work, such as a script or a codemod, instead of working by hand. |
| Architecture | [Model the Domain](./skills/principle-model-the-domain/SKILL.md) | Encode the domain in a structure, such as a state machine or a table, instead of scattered conditionals. |
| Architecture | [Boundary Discipline](./skills/principle-boundary-discipline/SKILL.md) | Put guards at system boundaries, trust internal types, and keep business logic pure. |
| Architecture | [Type System Discipline](./skills/principle-type-system-discipline/SKILL.md) | Make illegal states unrepresentable, brand primitives, and parse external data at boundaries. |
| Architecture | [Make Operations Idempotent](./skills/principle-make-operations-idempotent/SKILL.md) | Make a command or a loop reach the same end state after crashes and retries. |
| Architecture | [Migrate Callers Then Delete Legacy APIs](./skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | Migrate every caller and delete the old API in one wave. |
| Architecture | [Separate Before Serializing Shared State](./skills/principle-separate-before-serializing-shared-state/SKILL.md) | When concurrent actors might write the same thing, remove the sharing first. |
| Verification | [Prove It Works](./skills/principle-prove-it-works/SKILL.md) | Before declaring done, check the real artifact, not a proxy or "it compiles". |
| Verification | [Fix Root Causes](./skills/principle-fix-root-causes/SKILL.md) | Reproduce first, trace each symptom to its root cause, and fix it there. |
| Verification | [Sequence Work into Verifiable Units](./skills/principle-sequence-verifiable-units/SKILL.md) | Break multi-step work into small units that each end in a check, and verify each before the next. |
| Verification | [Test Behavior, Not Implementation](./skills/principle-test-behavior-not-implementation/SKILL.md) | Call the code the way its users do and compare the result with a literal expected value. |
| Verification | [The Baseline Is the Contract](./skills/principle-baseline-is-the-contract/SKILL.md) | Copy a settled answer, prototype or signed-off page exactly, and raise a gap to whoever owns it. |
| Verification | [Run the Smallest Test Set](./skills/principle-run-the-smallest-test-set/SKILL.md) | Run the smallest test set that proves the change, and a full suite only for a gate or a named risk. |
| Verification | [Explain the Number](./skills/principle-explain-the-number/SKILL.md) | Before you trust a measured number, find what limits it and rule out that it measured something else. |
| Delegation | [Guard the Context Window](./skills/principle-guard-the-context-window/SKILL.md) | Send bulk work to subagents and keep summaries in the main thread. |
| Delegation | [Never Block on the Human](./skills/principle-never-block-on-the-human/SKILL.md) | Do reversible work and show the result, and ask only about a decision that belongs to the owner. |
| Delegation | [Progress Is What the Record Says](./skills/principle-progress-is-what-the-record-says/SKILL.md) | Where work stands is what the ticket, branch, map or resume note says, not what the session remembers. |
| Writing | [Write for Where It Is Read](./skills/principle-write-for-where-it-is-read/SKILL.md) | Before writing, name who reads the text, what they are doing then, and what they can see. |
| Writing | [Anchor Every Reference](./skills/principle-anchor-every-reference/SKILL.md) | Name a file, section, rule or event by its path and its heading, identifier or rule number, the same way each time. |
| Writing | [Files Describe the Present](./skills/principle-files-describe-the-present/SKILL.md) | Write only what is true now. What changed and why goes in the commit message and the reply. |
| Meta | [Encode Lessons in Structure](./skills/principle-encode-lessons-in-structure/SKILL.md) | When you write the same instruction a second time, encode it as a lint, a flag, a runtime check or a script. |

## Models

The `dispatch` skill sends sessions in six roles, listed in [`roles.json`](./skills/dispatch/roles.json): `junior-worker`, `senior-worker`, `reviewer`, `researcher`, `candidate` and `advisor`. Each role is one row of `~/.mmw/models.json`, which names its host, its model and its reasoning effort. The same file names the runner that starts the sessions.

Change it only with `models.py config`. A change takes effect at the next session start, with no restart and no reinstall.

```bash
python3 mmw-v4/skills/dispatch/scripts/models.py config show
python3 mmw-v4/skills/dispatch/scripts/models.py config set <role> <host> <model> <effort>
python3 mmw-v4/skills/dispatch/scripts/models.py config runner <orca|herdr|paseo|auto>
```

[`editing-models.md`](./skills/dispatch/references/editing-models.md) explains each command and the limits of each host.

## License

MIT
