# AGENTS.md

MMW is the user's toolbox of skills shared across hosts, repositories and machines, together with the landing pipeline behind them (spec → ticket → a worker dispatched for the night → closed ticket) and a local task board. Personal use, no CI, tests run by hand.
Only `mmw-v3/` is live. It is built on pstack's layout: every session reads the `mmw-mode` skill, whose `## Playbooks` routes each task to one playbook (ADR 0032). `mmw-v2/` and `archive/` are earlier generations, `deprecated/` what v2 retired, `docs/research/code-landing-refs/` read-only snapshots of third-party repositories: read them for history, treat nothing in them as fact, and leave their scripts unrun. The rest of `docs/research/` holds research notes, which a spec may cite as sources.
This repository is also a consuming repository of its own pipeline: root `.mmw/` holds the task board's product answers, `docs/specs/task-board/screen-contract.yaml` is its screen contract, `prototypes/` its design package. Tickets about the board run from here.
The skills in this repository are deliverables, not the working instructions of an agent working on it.

## Self-hosting boundary

When this repository consumes its own landing pipeline, the MMW runtime for the whole run is the checkout recorded in `~/.mmw/installed-root` when the night or one-ticket watch opens. Treat that installed checkout, its skills, scripts, prompts, event vocabulary, relay and watchdog as one frozen version until the watch closes.

- Everything under the ticket worktrees, merge worktrees, main worktree, project branch and base branch is the product being changed. Never run its copy of an MMW skill or script to control, interpret, repair or finish the run that is changing it. In particular, do not call a repo-local `dispatch.sh`, `verify-ticket.py`, `events.py`, migration or replacement closeout protocol because it has just landed on the base branch.
- Do not move `.worktrees/mmw-installed`, run `install.sh`, retarget installed symlinks, change the live model configuration to satisfy new code, or otherwise make a running watch consume any part of the version it is building. A passing ticket, an already-landed dependency, a test result and an agent's judgement are not exceptions.
- Tests of the changed MMW run only in isolated test homes against fake trackers, runners and repositories. They prove the product under test; they do not authorize that product to take over the current run. The changed MMW becomes eligible to run only after the old installed MMW has closed the whole watch, the user has accepted the result, `finish` has completed, and the installed checkout is deliberately updated for a later run.
- If the frozen runtime cannot finish a batch after the product under test changes a protocol, do not bridge the versions by editing events, invoking the new protocol or resuming an agent under new instructions. Keep the old runtime authoritative and report the incompatibility immediately. Suspend or repair the run only through that frozen runtime; record the product defect for a later batch.

## Package Manager

No package manager, no build step. Runtime is bash and the `python3` standard library; scripts with a PEP 723 dependency block and some suites run under `uv run`; gate-check's tests and the board's need `node`; the board, ui-acceptance, design-pages and write-screen-contract tests need Playwright's browsers.

## Commands

| Command | What it does |
| --- | --- |
| `bash mmw-v3/install.sh` | The one install entry. Its header comment lists the nine items it installs: every directory under `mmw-v3/skills/` with a `SKILL.md`, symlinked into `~/.agents/skills` and `~/.claude/skills`; the host hooks; the user-level prompt; a launchd task watching it; the `com.mmw.board` LaunchAgent; Paseo's configuration and a default `~/.mmw/models.json` when absent; Orca's `worktree-base-path`; the Nowledge Mem Space and Identities; the `nowledge-mem` entry in `~/.cursor/mcp.json`. It removes what v2 installed and v3 does not, and records this checkout's `mmw-v3/` in `~/.mmw/installed-root` |
| `bash mmw-v3/install.sh --check` | Read-only: exit 0 when complete, 1 when something is missing or stale. Run from another checkout it hands over to the installed checkout's own `install.sh` and only reports. `dispatch.sh check <spec>` runs it before every night and reports what remains as a warning |
| `python3 mmw-v3/prompt/render.py --adopt` | Once per machine: the `AGENTS.md` already at a target is not a generated file, and `render.py` refuses to overwrite it otherwise |
| `bash mmw-v3/prompt/tests/run.sh` | Tests `render.py`; needs only `python3` |
| `bash mmw-v3/tests/<name>/run.sh` | One suite: `board`, `design-pages`, `dispatch`, `exe-release`, `install`, `liveness`, `manage-agents-md`, `relay`, `retro`, `setup-mmw`, `ui-acceptance`, `verify-ticket`, `write-screen-contract`, and `lib` for the shared checks themselves. There is no aggregate runner; each `run.sh` header names what it tests and what it needs. Every suite first runs the three shared checks in `mmw-v3/tests/lib/`: `check_module_paths.py` (a script names a module file that is gone), `check_wiring.py` (a route, principle line, or a skill, file, script or `dispatch.sh` command a step names is missing), `check_skill_frontmatter.py` under `uv run` (invalid YAML, or a key beyond `name` and `description` on one of this repository's skills); every suite therefore needs `uv` |
| `bash mmw-v3/tests/dispatch/test_dispatch.sh <scenario>` | One dispatch scenario (about two hundred; `all` runs them all, `install` the install scenarios that `mmw-v3/tests/install/run.sh` runs); `mmw-v3/tests/relay/test_relay.sh` takes the same argument |
| `python3 mmw-v3/check_imports.py` | Checks `mmw-v3/imports.tsv` against `mmw-v3/skills/`: every file has a row, every source is readable at its commit, a file with no recorded edit is byte-identical to its source, and a file with recorded edits is unchanged since the commit that last changed its row. Prints `IMPORTS OK <n> rows` |
| `python3 mmw-v3/skills/dispatch/scripts/check-interfaces.py` | Checks that the dispatcher's side and the agent's side of every role meet: start prompts, relay wakes, playbook steps, `RESUME:` titles, `roles.json`. Prints `INTERFACES OK` |
| `python3 mmw-v3/skills/dispatch/scripts/models.py config show\|set\|runner …` | The only way to change `~/.mmw/models.json` (which host, model and reasoning effort each role runs on; the selected runner). Takes effect at the next start, no restart or reinstall. Usage in `mmw-v3/skills/dispatch/references/editing-models.md` |

## External References

| Need | File |
| --- | --- |
| The terms of the landing pipeline and the toolbox, split into bounded contexts; read the map before changing vocabulary | `CONTEXT-MAP.md`, then `docs/contexts/<name>/CONTEXT.md` |
| ADR shape, the index, the translation table for two earlier numberings | `docs/adr/README.md` |
| Every `gh` operation of the issue tracker, the three label sets, the two morning queries | `docs/agents/issue-tracker.md` |
| The five triage roles and this repository's label strings | `docs/agents/triage-labels.md` |
| How to read the contexts and the ADRs before exploring code | `docs/agents/domain.md` |
| The night, step by step: `check`, `open`, `advance`, findings, Memory closing, `reverify`, `summary`, `retro`, `finish`, `suspend` | `mmw-v3/skills/mmw-mode/playbooks/run-a-night.md` |
| How the pipeline's machinery works underneath those commands: what `start` and `advance` do, events and holds, the relay's watches and wakes, the watchdog and turn guard | `docs/contexts/night/how-it-works.md` |
| The nine installed items, what v2 installed and install now removes | `mmw-v3/install.sh` header comment |
| Which prompt file reaches which host by which route, the generated file's shape, Grok's `[compat.claude]` requirement | `mmw-v3/prompt/README.md` |
| How the skill set is organised, where each part came from, how to add a playbook, principle or skill | `mmw-v3/skills/README.md` |
| Every rule for the text of a skill, playbook or reference, and the commands that pull an upstream's new version; read before writing, editing or reviewing one | `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` |
| How code in this repository is written; the reviewer's Standards axis applies it | `CODING_STANDARDS.md` |
| Where the tests live, how they are isolated, which suites a change needs; the reviewer's Tests axis applies it | `TESTING.md` |

## Key Conventions

- Every directory under `mmw-v3/skills/` with a `SKILL.md` is installed; there is no second list. A host's symlink points at the skill's directory in the installed checkout (see Gotchas), so a released edit is live at the next call; only the frontmatter `description` is scanned at host start and needs a new session.
- A playbook, a principle and a skill are each registered once: a route line in `mmw-mode`'s `## Playbooks`, a line in its `## Principles`, or the skill's directory. `check_wiring.py` holds the set to it.
- Upstream text enters by copy, not by link. `mmw-v3/upstream-mattpocock/`, `mmw-v3/upstream-pstack/` and `mmw-v3/upstream-diagram-design/` are read-only squash subtrees; a file copied from one into `mmw-v3/skills/` gets a row in `mmw-v3/imports.tsv` naming its source and commit, and every edit to it a `J` judgement entry in that row. gate-check under the `verify-ticket` skill came from Leonxlnx/unlazy and is owned here, not pulled again.
- Every git worktree the pipeline makes sits under the main worktree's `.worktrees/`: `issue-<n>` per ticket, `merge-<branch>` per merge target with one lock each; those names belong to the pipeline. This checkout also carries one hand-made worktree, `mmw-installed`, a full checkout.
- The user-level prompt is edited in `mmw-v3/prompt/shared.md`, read by Claude Code, Codex and Grok. `~/.codex/AGENTS.md` and `~/.grok/AGENTS.md` are generated, and `render.py` refuses to overwrite a hand edit. Cursor's user-level prompt is maintained in the app.

## Gotchas

- This machine's install is served from the installed checkout `.worktrees/mmw-installed` (recorded in `~/.mmw/installed-root`), and every host symlink points there: an edit to a `SKILL.md` or script in the main worktree reaches no host until it is released. A change is finished only when all four promotion steps have run, in this order: commit on `dev`; fast-forward `main` to it (`git push . dev:main`); move the installed checkout to `main` (`git -C .worktrees/mmw-installed checkout --detach main`) and confirm with `bash mmw-v3/install.sh --check`; push both (`git push origin dev main`). The third step waits while any watch is open (Self-hosting boundary). `install.sh` runs only when the user explicitly authorises it; its read-only `--check` is the exception.
- With Claude Code's Bash sandbox on, the PreToolUse hook `install.sh` registered cannot open the symlink target under `~/.agents/skills` and blocks every command with `can't open file '…/dispatch/scripts/tool-guard.py'`. The file is there; the same command passes with the sandbox off. Leave the install alone.
- Each Codex hook needs a `trusted_hash` line in `~/.codex/config.toml`; `install.sh` computes it with Codex's own algorithm. When Codex changes the algorithm it prompts "hooks need review" again and `--check` cannot tell.
- Both dispatch hooks decide whether to stand down from the host's own payload fields, never from the environment: Cursor and Grok export their variables into every child process, and an environment test would also switch off the hooks of a Claude session started from one of their panes.
- A skill directory is one symlink shared by every repository on the machine: a credential written into any file under its `scripts/<…>` is loaded by every other run.

<important if="you are opening a night or working one ticket inside this repository">
- `dispatch.sh start` cuts the ticket worktree under the main worktree's `.worktrees/` whichever worktree it is run from, so a worker starts its reviewer from its own worktree and both work in the same place.
- This repository's `.mmw/target.json` has no `checks` key; `advance`'s merge step says so on stderr. Known, not a fault.
</important>

<important if="you are pulling an upstream's new version or editing a file copied from one">
- Follow the upstream-update bullets of `mmw-v3/skills/mmw-mode/references/skill-set-rules.md`: pull the subtree, `grep -n '<source path>' mmw-v3/imports.tsv` for every row a changed upstream file touches, carry each change in or record why not as a `J` entry, move the row's commit forward, and finish with `python3 mmw-v3/check_imports.py`.
</important>

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
