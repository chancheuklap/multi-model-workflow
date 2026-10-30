### Set up code checkers

**You own one repository's `scripts/check`: the one executable at its root that runs its checkers and its tests in three tiers, the checkers it runs installed so a fresh clone or a new worktree has them at the right version without anyone remembering to install anything, and the commit hook that runs the fastest tier.** Run it when a repository has no `scripts/check`, when a language, a sub-project or a checker is added to one that has it, when a checker it uses was superseded (pyright, eslint, tsc --noEmit, black, isort), or when the setup-mmw skill sends you here. Where each tool goes and which tool is chosen are decided by **The rule that decides where a tool goes**, **What to install** and **Pin the formatter exactly, the checkers loosely** below. Distinct from the `setup-mmw` skill, which checks a repository's whole setup and sends you here for this one item.

Who depends on what you build: `dispatch.sh land` runs the default tier on each merge result, and the orchestrator runs it before pushing a closing-pass fix. The commit hook runs `--staged`. `dispatch.sh summary` runs `--all` at the night's end, One ticket runs it before its pull request, and setup-mmw runs it once when connecting a repository. A green full run is recorded on the spec for `finish` to reuse. The default tier is the check a commit made with `--no-verify` still passes through. A tier that reports green while checking nothing lands broken work under a green mark on every ticket after it. A tier that is red on old debt, or too slow, blocks every ticket or teaches everyone to skip it. This session writes, commits and pushes the change itself: `dispatch.sh open-ticket` and `land` refuse a repository with no `scripts/check`, so this change cannot land through a ticket.

1. **Read what the repository already runs.** Its check commands and scripts (the manifest's scripts, a `Makefile`, the scripts under its scripts directory, the `## Commands` table of `AGENTS.md`), its commit hooks (`.pre-commit-config.yaml`, `git config core.hooksPath`) and its CI workflows. Run each once from the repository root. Find every test root: `tests/` and each directory like it, every `package.json` with a `test` script, each sub-project with a runner of its own; and every test that needs a device or a real credential. Count the files per language: a language with a handful of files does not need a checker. A command that already works is wrapped by `scripts/check`, not rewritten (**principle-start-from-what-exists**).
   Done when you hold each existing command with whether it passes on the branch checked out, and its first failing line when it does not; each test root with the test groups under it; and which languages get checkers.
2. **Add each missing tool to the project manifest** and install (`uv sync`, `pnpm install`).
   Done when each tool is in the manifest and installed.
3. **Configure** — per-language detail in the `mmw-mode` skill's `references/checkers-python.md` and `references/checkers-typescript.md`.
   Done when each tool runs with the repository's configuration.
4. **Reduce a first run to real findings.** A first run on an existing codebase reports thousands. Almost none of it is worth a human's attention, and reading it in the order the tool printed it is how the whole effort gets abandoned. Separate it in this order:

   1. **Misconfiguration.** Import roots the checker cannot resolve, dependencies absent by design on this platform, framework idioms the rule was not written for. This is usually most of the count. Fix the config, not the code — and exempt precisely: a framework's specific calls, not the whole rule.
   2. **Machine-fixable.** Run the fixer. Import order, dead suppressions, obsolete syntax — the diff is large and needs no reading.
   3. **The formatter, by one rule.** A repository with no open branches and no tickets in flight gets one commit that reformats every file; add that commit's hash to `.git-blame-ignore-revs`. Any other repository formats newly added files only: reformatting an existing file collides with every open branch that touches it.
   4. **What's left is the real backlog — and it must never block a commit** (**principle-subtract-before-you-add**). A checker that reports a file's existing problems every time someone edits one line of it has one outcome: everybody starts passing `--no-verify`, and the checker no longer checks anything. Two mechanisms, depending on what the tool offers:

      - **A checker baseline**, when the tool has one (type checkers usually do). Existing errors go in it and stay quiet; anything new is reported from day one. Commit the baseline — it belongs to the branch like the config does. Prefer this over the tool's bulk-suppress command, which writes an ignore comment at every site: thousands of lines of source noise to say nothing.
      - **Filter to the changed lines**, when it does not. Run the linter with JSON output, intersect its line numbers with `git diff --unified=0`, report only the overlap. Two traps: the linter reports absolute paths while git reports repository-relative ones, so normalise before comparing; and untracked files appear in no diff at all, so pull them in separately and treat every line as new.

      The point of both is that the checker is **useful on day one** rather than after a cleanup nobody schedules. This holds for every checker in the set, including one that must see a whole package, and for every tier of `scripts/check`: the default tier checks what this branch changed against its base, `--all` the whole tree, and a fix flag rewrites only the files that scope selects. Probe it the other way too: add one clean line to a file that already has findings, and confirm the hook and the default tier both pass.

   Done when what is left of the first run is in a baseline or behind the changed-lines filter.
5. **Probe every checker.** A checker fails silently in three ways, and each reports the same zero as a clean repository: it never found its engine, its baseline swallows the new error, or its paths exclude the directory the code is in. Aim each probe at the mechanism you would otherwise be trusting: plant one in every directory that holds code of that language, including those outside the package layout (scripts, test harnesses, extensionless executables), and run the probes from a fresh worktree, which is where agents commit from. Reviewers skip what tooling enforces, so a directory no checker covers is checked by nobody. For each one, write a file that must fail, run the checker on it, confirm it fails, delete it: a new type error in a new file for a type checker with a baseline (the baseline must not cover it); a floating promise, or anything else undecidable without type information, for a type-aware linter; an unclosed tag and an image without alt text for a template linter; a badly formatted file that `--check` rejects for a formatter. Report each checker's count and its probe result (**principle-test-behavior-not-implementation**).
   Done when every checker reported a planted defect.
6. **Declare each step's inputs.** Every step of the default tier, each checker and each test group, runs exactly when a changed path lies among its inputs: the paths whose change can change its result. There is no always-run group and no step that runs whatever changed. A test group's inputs are the files its tests import, computed by `scripts/check` from the test files at each run wherever the language allows it (an import walk over the test files for Python, `vitest related` for Vitest), plus each path its tests read, run or compare as generated output, declared by hand, one line per path naming the test that reads it. A whole-program type check or build declares every source file of its language and its configuration; a check that walks the whole tree declares the whole tree, and so runs on every change because its result can change with any. A prefix that stands for a layer (`src/`, the shared test helpers, every group of one language) is not an input: a group runs only on paths its tests can reach. A small suite stays one group whose input is its package; a large one splits by what its tests reach, so that one change selects few. Every directory under a test root is in a group or listed as excluded with its reason. List `tests/e2e/` as excluded because its tests belong to the verification system and run through the CHECK line supplied by the `verify-<product>` skill's Launch, not through `scripts/check`. A test that needs a device or a real credential is in no tier and goes on the `not run here:` line. Time each group once after the install; the seconds go into the commit message of step 10, not into any file, and tell you which group to split. No tier kills a step or fails it for running long, since a slow test is not a broken one.
   Done when every step of the default tier has its inputs declared or computed, every directory under each test root is in a group or excluded, and a change to a file no input names (a README) selects no step.
7. **Write `scripts/check`**, one executable that runs everything, reporting only, with a flag for the fixes that are safe to apply. It is the one command a reviewer, a worker and the pipeline rerun (**principle-build-the-lever**). Its tiers:

   | Tier | Runs | Run by |
   | --- | --- | --- |
   | `scripts/check --staged` | one line handing over to the commit-hook tool (`exec prek run`); it carries no second list of checkers | the commit hook, and anyone who wants the commit's checks without committing |
   | `scripts/check` | each step whose inputs hold a path changed against the base, `git diff --name-only "$MMW_BASE_REF"...HEAD` plus uncommitted and untracked changes: lint and type checks on those files, then the selected test groups; the repository's own idempotent dependency install (`uv sync`, `pnpm install --frozen-lockfile`) runs first when a selected step needs it | `dispatch.sh land` on each merge result, and the orchestrator before a closing-pass push |
   | `scripts/check --all` | the install, then everything runnable on this machine | `dispatch.sh summary` at the night's end, One ticket before its pull request, and setup-mmw once |

   Its readers are agents with little attention to spare (**principle-fail-loudly**):
   - The base is `MMW_BASE_REF` when it is set, so a ticket cut from any branch is compared against the branch it merges into; otherwise the repository's base branch, named in the script's header.
   - Its header comment is where an agent learns how this repository is checked: the three tiers, the exit codes, the base, the commit hook and how to skip it.
   - Exit 0 is a pass; 1 the product is red; 2 the environment cannot run the check: a missing tool, service or dependency, or an install that failed. Decide pass or fail by each tool's exit code, never by a printed summary; some tools print none.
   - One line per selected step before it runs, `SELECT <step>: <changed path> (<input>)`, naming one changed path and the input entry that selected it; one line saying so when nothing is selected.
   - One line per step, `PASS <step> <seconds>s` or `FAIL <step> <seconds>s`. A failing step adds its last lines and the path of its full log, under `.scratch/check/`. Every tier prints one line `not run here: …` naming the tests in no tier, and ends with a one-line summary.
   - A self-check exits 1 when a directory under a test root is neither in a group nor listed as excluded, naming the directory and where in `scripts/check` to add it.

   Done when every tier passes on the repository as it stands, or the reply names each red step of `--all` with its first failing line.
8. **Prove each tier red.** Plant one defect per tier and read its exit code (**principle-test-behavior-not-implementation**, **principle-fail-loudly**): a lint error staged for `--staged`; a failing test in one group's area, committed on a scratch branch and run with `MMW_BASE_REF` at its parent, for the default tier, confirming that only the steps whose inputs hold that path ran; a one-line change to a file no input names, confirming the default tier ran no step; a failing test in a group the default tier would not select, for `--all`; a tool the install needs removed from `PATH`, for exit 2; a new directory under a test root, for the self-check. Then remove every probe.
   Done when each probe gave its expected exit code and the tree is back where it started.
9. **Run them at commit time** — the `mmw-mode` skill's `references/checkers-git-hooks.md`. Wire this even when per-agent automation is out of scope, because it is not per-agent.
   Done when a probe commit was refused as `references/checkers-git-hooks.md` `## Probe it with a real commit` describes.
10. **Commit and push.** One commit on the branch checked out, holding every file this run wrote; its message gives each test group's measured seconds and each tier's total. Push it: ticket worktrees are cut from `origin`, so a `scripts/check` only on this machine is one no merge runs.
    Done when the commit is on `origin`, or the reply says why it is not.

The whole run is done when, from a fresh worktree, every checker reports a defect planted in each directory it covers, each tier exits 1 on its planted defect and 2 with a tool missing, a one-line clean edit to a file with existing findings passes both the hook and the default tier, and a probe commit is refused.

**The rule that decides where a tool goes.** **A tool whose version changes what the repository produces belongs to the repository.** A formatter reflows files; a linter's ruleset decides what passes; a compiler decides what ships. Install those through the project's own dependency manifest, so checking out a branch checks out the checkers that branch was written against.

Everything else — the editor, the agent CLI, `ripgrep`, `docker` — belongs to the machine. Installing a checker globally is the failure this rule prevents: a new worktree silently has none, a second machine has a different one, and when the global tool upgrades every branch fails at once with no commit to blame.

**What to install.**

| Language | Tool | Manifest | Reference |
| --- | --- | --- | --- |
| Python | `ruff` (lint **and** format) | `[dependency-groups] dev` | `references/checkers-python.md` |
| Python types | `pyrefly` | same | `references/checkers-python.md` |
| Jinja / Django templates | `djlint` | same | `references/checkers-python.md` |
| TypeScript / JavaScript | `oxlint` + `oxlint-tsgolint` | `devDependencies` | `references/checkers-typescript.md` |
| Shell | `shellcheck`, `shfmt` | machine — no language manifest owns them | — |
| Running them at commit time | `prek` | machine, same reason | `references/checkers-git-hooks.md` |

Settled choices, and the fact that decides each:

- **`pyrefly`, not `pyright`** — pyright needs Node and is an order of magnitude slower on a full check. **Not `ty`** — it has not reached a stable release and fails part of the typing conformance suite; fine as an editor server, not as a gate. Re-check both facts against the tools' own release pages before repeating them to a user.
- **`oxlint`, not `eslint`** — TypeScript 7 ships no stable programmatic API, so `typescript-eslint` cannot run on it. `oxlint-tsgolint` embeds the TS 7 engine itself.
- **No separate `tsc --noEmit`** — `oxlint --type-aware --type-check` shares one TypeScript program between the lint pass and the type pass.
- **`ruff` replaces black, isort, flake8, pyupgrade, bandit** — one binary, and the format and lint passes agree with each other by construction.

**Pin the formatter exactly, the checkers loosely.** A formatter's output changes between patch releases. Two branches formatted by two versions produce whole-file diffs that collide on every merge, so pin it to an exact version. A linter's new release only adds diagnostics — it rewrites nothing — so a compatible range is right, and keeps the tool moving.

Pin exactly, too, anything whose version is coupled to another tool's; a range drifts off the tool it has to match.

Upgrading is then one deliberate act: bump, run everything, absorb the changes in one commit.

**Reply:** each checker installed, the manifest that holds it and its pinned version or range; each checker's first-run count and what was left in a baseline or behind the filter; each probe result; each step's inputs and how they are found; each test group's measured seconds and each tier's total; each tier's planted-defect result; the hook and how to skip it; and the commit and branch of step 10.
