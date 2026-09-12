# AGENTS.md

MMW is the user's toolbox of skills shared across hosts, repositories and machines, together with the landing pipeline behind them (spec → ticket → a worker dispatched for the night → closed ticket) and a local task board. Personal use, no CI, tests run by hand.
Only `mmw-v2/` is live. `archive/` is the previous generation, `deprecated/` what v2 itself retired, `docs/research/` read-only snapshots of third-party repositories: read them for history, treat nothing in them as fact, and leave their scripts unrun.
This repository is also a consuming repository of its own pipeline: root `.mmw/` is the task board's acceptance runtime, `docs/specs/task-board/screen-contract.yaml` its screen contract, `prototypes/` its handoff package. Tickets about the board run from here.
The skills in this repository are deliverables, not the working instructions of an agent working on it.

## Package Manager

No package manager, no build step. Runtime is bash and the `python3` standard library; scripts with a PEP 723 dependency block and some suites run under `uv run`; the claude-design-blocks, verify-ticket and gate-check tests need `node`; the board and drive-target tests need Playwright's browsers.

## Commands

| Command | What it does |
| --- | --- |
| `bash mmw-v2/install.sh` | The one install entry, eight items: skill symlinks into `~/.agents/skills` and `~/.claude/skills`; hooks into each host's own configuration (drive-target's `hook.py`, dispatch's turn guard `turn-guard.py`; Codex trust hashes into `~/.codex/config.toml`); user-level prompts (`~/.claude/CLAUDE.md` → `mmw-v2/prompt/shared.md`, `~/.claude/rules/mmw-claude.md` → `mmw-v2/prompt/hosts/claude.md`, one AGENTS.md each for Codex, Pi and Grok rendered by `mmw-v2/prompt/render.py`); a launchd task watching the prompt sources; the `com.mmw.board` LaunchAgent keeping `mmw-v2/board/supervisor.py` alive; Paseo configuration (`~/.local/bin/paseo`, grok/cursor providers and `worktrees.root` in `~/.paseo/config.json`, no Agent profiles; `~/.mmw/models.json` written with defaults only when absent, a legacy Markdown file imported once and deleted); Orca setups' `worktree-base-path` set to `.worktrees`; the `nowledge-mem` entry in `~/.cursor/mcp.json`. It records this checkout in `~/.mmw/installed-root` |
| `bash mmw-v2/install.sh --check` | Read-only: exit 0 when complete, 1 when something is missing or stale. Run from another checkout it hands over to the installed checkout's own `install.sh` and only reports. It also reads each runner adapter's `# MMW_USES:` header and asks the binary on `PATH`: `没查` when the help page is unreadable, `不一致` when a flag is gone; a binary absent from `PATH` skips that adapter silently. `dispatch.sh check <spec>` runs it before every night |
| `python3 mmw-v2/prompt/render.py --adopt` | Once per machine: the AGENTS.md already at a target is not a generated file, and `render.py` refuses to overwrite it otherwise |
| `bash mmw-v2/prompt/tests/run.sh` | Tests `render.py`; needs only `python3` |
| `bash mmw-v2/tests/<name>/run.sh` | One skill's or subsystem's suite, ten of them: `verify-ticket`, `drive-target`, `align-screens`, `dispatch`, `exe-release`, `manage-agents-md`, `claude-design-blocks`, `board`, `liveness`, `relay`. `advisor`, `code-checkers` and `verdict` have none. There is no aggregate runner; each `run.sh` header names what it tests and what runtime it needs (the `board` one does not: `uv`, Playwright and a real headless Chromium) |
| `bash mmw-v2/tests/dispatch/test_dispatch.sh <scenario>` | One dispatch scenario (about seventy; `all` runs them all); `mmw-v2/tests/relay/test_relay.sh` takes the same argument |
| `bash mmw-v2/hooks/tests/run.sh` | Tests `rule-at-moment.py`, a hook kept in the repository that `install.sh` leaves alone; whoever wants it registers it by hand under `~/.claude/hooks/` |
| `cd mmw-v2/skills/verify-ticket/scripts/gate-check/tests && node run-tests.mjs && node lint-tests.mjs` | The tests that came with gate-check from unlazy (the vendored layer); `verify-ticket`'s `run.sh` runs them too |
| `python3 mmw-v2/skills/dispatch/scripts/models.py config show\|set\|runner …` | The only way to change `~/.mmw/models.json` (which host, model and effort each agent runs on; tonight's runner). Takes effect at the next start, no restart or reinstall. Usage in `mmw-v2/skills/dispatch/references/editing-models.md` |

## External References

| Need | File |
| --- | --- |
| Every fixed word of the landing pipeline and its interface record (event names, command signatures, constant tables), split into six bounded contexts; read the map before changing vocabulary | `CONTEXT-MAP.md`, then `docs/contexts/<name>/CONTEXT.md` |
| ADR shape, the index, the translation table for two earlier numberings | `docs/adr/README.md` |
| Every `gh` operation of the issue tracker, the three label sets, the two morning queries | `docs/agents/issue-tracker.md` |
| The five triage roles and this repository's label strings | `docs/agents/triage-labels.md` |
| How to read the contexts and the ADRs before exploring code | `docs/agents/domain.md` |
| The night runbook: `check`, `open`, `advance`, the closing pass, `reverify`, `summary`, `finish`, `suspend`, each with its exit codes | `mmw-v2/skills/dispatch/references/night.md` |
| How the pipeline's machinery works underneath those commands: what `start` and `advance` do, events and holds, the relay's watches and wakes, the watchdog and turn guard | `mmw-v2/skills/dispatch/references/how-it-works.md` |
| The eight installed items, the two modes, what the previous generation installed and install now removes | `mmw-v2/install.sh` header comment |
| Which prompt file reaches which host by which route, the generated file's shape, Grok's `[compat.claude]` requirement | `mmw-v2/prompt/README.md` |
| Pulling an upstream subtree, resolving conflicts, the `disable-model-invocation` pairing rule, the three host-neutral rewrites | `mmw-v2/merge-notes/README.md` |
| When a downstream-note is due and its three fixed headings | `mmw-v2/downstream-notes/README.md` |
| gate-check's source commit, which files are byte-identical, which lines were changed | `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md` |

## Key Conventions

- A `SKILL.md` is one text for every host and every runner: no host is default or preferred, nothing branches on a host or runner name, and a capability difference is written as the capability ("a host that cannot hold a turn", "a host that can run subagents"). Tonight's runner is whatever `models.py runner` selects (its last step is a default); the text states that selection and assumes nothing past it. A runner's own commands live only in its adapter `mmw-v2/skills/dispatch/scripts/runners/<runner>.sh`, whose `# MMW_USES:` header is the authoritative list of what it calls. The frontmatter `description` names no runner: every host scans it into its system prompt, so one name locks the skill to that runner; a runner that cannot start is refused by one stderr line at run time.
- `mmw-v2/skills.txt` alone decides which skills are installed. A host's symlink points straight at the source directory, so an edit is live at the next call; only the frontmatter `description` is scanned at host start and needs a new session.
- A skill directory `mmw-v2/skills/<name>/` is symlinked whole into every host, so it holds only what the agent holding the skill reads or runs: `SKILL.md`, reference files, `scripts/<…>`. Its tests live in `mmw-v2/tests/<name>/`, which exists only in a checkout and climbs two levels to `mmw-v2/` and down into `skills/<name>/scripts/` to reach the script under test. The one exception is the whole of `mmw-v2/skills/verify-ticket/scripts/gate-check/`, copied entire from unlazy with its own tests and the `UPSTREAM.md` that records source, commit and every local edit; no subtree, no merge-note, and the directory itself is the only lead the next person comparing against unlazy has.
- A skill's scripts are resolved by the agent holding the skill, from its `SKILL.md`, as `scripts/<…>`; a caller names the skill and the job, never an install path. A ticket's `CHECK:` line names no path either: a shell runs it with no agent in between, and `verify-ticket.py` puts the drive-target skill's `scripts/<…>` on that shell's `PATH` (`--tools`), so a judge is named bare. A judge no directory in force holds is refused, exit 2, before any criterion runs, because `command not found` reads exactly like a criterion that ran and failed. Shapes in `mmw-v2/skills/drive-target/references/boundary-check.md` and `story-parity.md`.
- A skill refers to its own or a sibling skill's scripts through one token, defined once in a section headed `` ## Resolve `<token>` once `` that says what the token expands to in every command below and resolves it from the file's own location; one section may define several tokens. The body carries no bare relative path and no undefined token. A token naming an executable (`<engine>`, `<dispatch>`, `<events.py>`, `<lease.py>`, `<release>`) resolves to exactly one file across the toolbox, because an agent holding several skills reads all their vocabulary as one. The directory token `<scripts>` is each skill's own; a skill reaching into drive-target's directory writes `<drive-target scripts>`.
- An absolute path in prose or a command is legal in three cases only: (a) a fixed user-level location (`~/.mmw/models.json`, `~/.agents/skills`, `~/.claude/skills`: the address on that machine, with no relative spelling); (b) a token's runtime expansion (`<dispatch>` becomes `bash <absolute path to dispatch.sh>` at run time and stays a token in text); (c) a path the run made itself (`mktemp`-derived, never a fixed name under `/tmp`). A script finds its neighbours from its own resolved location. Any other absolute path is a defect.
- A self-written skill ships no host-side manifest (upstream skills carry an `openai.yaml`; ours do not) and its frontmatter has exactly two keys, `name` and `description`: a skill's name and description have one authority.
- Which host, model and effort each agent runs on is written only in `~/.mmw/models.json` (under `MMW_HOME` when set), through `models.py config`; the task board writes the same file, under the same lock, with the same atomic replace. The first `install.sh` writes the defaults and later runs leave an existing JSON alone. `mmw-v2/skills/dispatch/hosts.json` records how each host starts and the first-install defaults, never tonight's choice. Neither file ever sits in a consuming repository. `dispatch.sh` resolves the row through `models.py` and hands it to tonight's runner adapter.
- `~/.mmw` holds two more things: `boards.json` (each consuming repository's main-checkout path → its task board's fixed port; `dispatch.sh board` writes it, `supervisor.py` reads it) and `state/<owner>__<name>/` (one 0700 directory per repository holding every file the relay, the watchdog and the turn guard keep, and not one byte of ticket state). The canonical reader of `MMW_HOME` is `home()` in `statedir.py`.
- A ticket's state is the fold of the `<!-- mmw {...} -->` blocks in its comments, in comment-id order. Every event is posted by a script; a model types none, so a `VERDICT` written with `gh issue comment` carries no block and counts for nothing. Agents wake each other through the relay, which turns ticket events into wakes: nobody polls, and the night has no clock.
- Landing is done on `origin/<base branch>`: `advance`, `land` and `reverify` merge, check and fast-forward push inside the persistent detached worktree `.worktrees/merge-<branch>`; a conflict or a red check becomes `ticket.bounced` for triage and leaves the base branch untouched. The base branch is cut from a project branch recorded in `spec.opened.project`; after the user accepts the night, `dispatch.sh finish <spec>` merges it back. Merging into the repository's default branch is not MMW's job.
- Every git worktree the pipeline makes sits under the main checkout's `.worktrees/`: `issue-<n>` per ticket, `merge-<branch>` per merge target with one lock each; those names belong to the pipeline. This checkout also carries hand-made worktrees (`mmw-installed`, `318-task-board`, `mmw-cursor`, `pi-canvas`), each a full checkout.
- Every refusal has the three parts `refusal.py` builds: what happened, with one checkable fact; why; what to do next. A check that could verify nothing says so instead of reading like a pass (ADR 0008). Script headers record dated, version-pinned measurements from real runs (each host's hook payload, each runner's liveness tolerance) rather than claims from documentation.
- User-level prompts are edited in `mmw-v2/prompt/shared.md` (shared by four hosts) and `mmw-v2/prompt/hosts/<host>.md` (one host). `~/.codex/AGENTS.md`, `~/.pi/agent/AGENTS.md` and `~/.grok/AGENTS.md` are generated, and `render.py` refuses to overwrite a hand edit. Cursor's user-level prompt is maintained in the app.
- The `nowledge-mem` entry in `~/.cursor/mcp.json` belongs to `install.sh`: its content comes from `nmem config mcp show --host cursor` with the `type` field removed, because `cursor-agent` reads only `url` and `headers` and skips the whole server when `type` is present (the symptom: a worker silently without memory tools). Other servers in the file are left as they are; a hand edit of this entry is overwritten at the next install and reported by `--check` first.
- `mmw-v2/upstream/` is a squash subtree of mattpocock/skills and `mmw-v2/upstream-diagram-design/` of cathrynlavery/diagram-design; both are edited in place. Upstream's own `AGENTS.md`, `CLAUDE.md` and `CONTEXT.md` (only `mmw-v2/upstream/` has them) stay as upstream wrote them; `mmw-v2/upstream/CONTEXT.md` is upstream's vocabulary; this repository's lives under `docs/contexts/` behind the root `CONTEXT-MAP.md`. A changed upstream skill gets its merge-note written or updated.
- A change here that invalidates a consuming repository's screen contract, ticket `CHECK:` or `.mmw/target.json` gets a downstream-note named after the ticket that caused it plus a slug.

## Gotchas

- This machine's install is served from the frozen worktree `.worktrees/mmw-installed` (recorded in `~/.mmw/installed-root`), and every host symlink points there: an edit to a `SKILL.md` or script in the main checkout reaches no host until that worktree is moved to the new commit or `install.sh` is rerun from the main checkout to take over.
- With Claude Code's Bash sandbox on, the PreToolUse hook `install.sh` registered cannot open the symlink target under `~/.agents/skills` and blocks every command with `can't open file '…/drive-target/scripts/hook.py'`. The file is there; the same command passes with the sandbox off. Leave the install alone.
- `MMW_V2_HOME` is a test seam for `install.sh` only: it moves the whole install target to a throwaway directory and skips `launchctl` and `paseo reload`. Runtime configuration goes through `MMW_HOME`.
- Each Codex hook needs a `trusted_hash` line in `~/.codex/config.toml`; `install.sh` computes it with Codex's own algorithm. When Codex changes the algorithm it prompts "hooks need review" again and `--check` cannot tell.
- Both hooks decide whether to stand down from the host's own payload fields, never from the environment: Cursor and Grok export their variables into every child process, and an environment test would also switch off the hooks of a Claude session started from one of their panes.
- A skill directory is one symlink shared by every repository on the machine: a credential written into any file under its `scripts/<…>` is loaded by every other run.
- `mmw-v2/upstream/CONTEXT.md` gives the label example `ready-for-afk` where this repository's label is `ready-for-agent`: a recorded, deliberate deviation, see `mmw-v2/merge-notes/README.md`.

<important if="you are opening a night or working one ticket inside this repository">
- `dispatch.sh start` cuts the ticket worktree under the main checkout's `.worktrees/` whichever worktree it is run from, so a worker starts its reviewer and verifier from its own worktree and they land in the same place.
- This repository's `.mmw/target.json` has no `checks` key; `advance`'s merge step says so on stderr. Known, not a fault.
- This repository's own changes are numbered tickets; the one that invalidates a consuming repository's artifacts lands with its downstream-note.
</important>

<important if="you are editing events.py or tree.py in verify-ticket, or ghlist.py or models.py in dispatch">
- The task board imports those four scripts by file path (`mmw-v2/board/board_data.py`, `settings_api.py`); a change to them is a change to the board. Run `mmw-v2/tests/board/run.sh` together with the `relay` suite.
</important>

<important if="you are pulling an upstream subtree or editing an upstream skill">
- Read `mmw-v2/merge-notes/README.md` first; resolve each conflict by the skill's merge-note entry, take upstream for passages no note covers, and finish with `bash mmw-v2/install.sh --check`.
- `disable-model-invocation` in `SKILL.md` and `policy.allow_implicit_invocation: false` in `openai.yaml` change together; this repository keeps them only on `setup-matt-pocock-skills`, `grill-me`, `handoff` and `wait-what`.
</important>

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
