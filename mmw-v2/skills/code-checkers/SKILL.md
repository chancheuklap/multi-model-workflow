---
name: code-checkers
description: Install and configure a repository's code checkers — linter, formatter, type checker — so their versions travel with the branch instead of the machine. Use when a repo has none, when a language is added to one that does, when a checker it uses was superseded (pyright, eslint, tsc --noEmit, black, isort), or when commits should run them through a pre-commit hook.
---

# Code checkers

Give a repository the checkers its languages need, wired so a fresh clone or a new worktree has them at the right version without anyone remembering to install anything.

## The rule that decides where a tool goes

**A tool whose version changes what the repository produces belongs to the repository.** A formatter reflows files; a linter's ruleset decides what passes; a compiler decides what ships. Install those through the project's own dependency manifest, so checking out a branch checks out the checkers that branch was written against.

Everything else — the editor, the agent CLI, `ripgrep`, `docker` — belongs to the machine.

Installing a checker globally (`uv tool install ruff`, `npm i -g eslint`, `brew install shellcheck`) is the failure this skill exists to prevent: a new worktree silently has no checker, a second machine has a different one, and the day the global tool upgrades, every branch fails its checks at once with no commit to blame.

## What to install

Count the files first — `find . -name '*.py' -not -path '*/.venv/*' | wc -l` and the same per extension. A language with a handful of files does not need a checker.

| Language | Tool | Manifest | Reference |
| --- | --- | --- | --- |
| Python | `ruff` (lint **and** format) | `[dependency-groups] dev` | [python.md](python.md) |
| Python types | `pyrefly` | same | [python.md](python.md) |
| Jinja / Django templates | `djlint` | same | [python.md](python.md) |
| TypeScript / JavaScript | `oxlint` + `oxlint-tsgolint` | `devDependencies` | [typescript.md](typescript.md) |
| Shell | `shellcheck`, `shfmt` | machine — no language manifest owns them | — |
| Running them at commit time | `prek` | machine, same reason | [git-hooks.md](git-hooks.md) |

Choices worth not relitigating, and the fact that decides each:

- **`pyrefly`, not `pyright`** — pyright needs Node and is an order of magnitude slower on a full check. **Not `ty`** — it has not reached a stable release and fails part of the typing conformance suite; fine as an editor server, not as a gate. Re-check both facts against the tools' own release pages before repeating them to a user.
- **`oxlint`, not `eslint`** — TypeScript 7 ships no stable programmatic API, so `typescript-eslint` cannot run on it. `oxlint-tsgolint` embeds the TS 7 engine itself.
- **No separate `tsc --noEmit`** — `oxlint --type-aware --type-check` shares one TypeScript program between the lint pass and the type pass.
- **`ruff` replaces black, isort, flake8, pyupgrade, bandit** — one binary, and the format and lint passes agree with each other by construction.

## Pin the formatter exactly, the checkers loosely

A formatter's output changes between patch releases. Two branches formatted by two versions produce whole-file diffs that collide on every merge, so pin it to an exact version (`ruff==0.16.5`). A linter's new release only adds diagnostics — it rewrites nothing — so a compatible range (`pyrefly>=1.0,<2.0`) is right, and keeps the tool moving.

Pin exactly, too, anything whose version is coupled to another tool's: `oxlint-tsgolint` version `7.0.2001` means TypeScript `7.0.2`, and a range would drift off the TypeScript the repo actually builds with.

Upgrading is then one deliberate act — bump, run everything, absorb the changes in one commit — instead of a failure on a day nobody planned for.

## Steps

1. **Count the files per language.** Install only for languages that need it.
2. **Add each tool to the project manifest** and install (`uv sync`, `pnpm install`). Never globally.
3. **Configure** — per-language detail in the reference files. Configure before looking at the error count: most of a first run is misconfiguration, not debt.
4. **Take the count down to signal.** Below.
5. **Probe every checker.** Below. A checker that reports zero because it never ran is worse than none.
6. **Write one entry point** that runs them all, reporting only, with a flag for the fixes that are safe to apply. Keep per-checker output to its summary line; a failing step prints its tail and the command to rerun for the full output.
7. **Run them at commit time** — [git-hooks.md](git-hooks.md). The git hook is the one place every author passes through: a person typing `git commit`, and every coding agent whatever its own hook format. Wire this even when per-agent automation is out of scope, because it is not per-agent.
8. **Record it where the next agent reads** — the repo's `AGENTS.md`: which tools, which manifest installs them, the one command, the commit hook and how to skip it, and that the type checker is baselined.

## Taking a first run down to signal

A first run on an existing codebase reports thousands. Almost none of it is worth a human's attention, and reading it in the order the tool printed it is how the whole effort gets abandoned. Separate it in this order:

1. **Misconfiguration.** Import roots the checker cannot resolve, dependencies absent by design on this platform, framework idioms the rule was not written for. This is usually most of the count. Fix the config, not the code — and exempt precisely: a framework's specific calls, not the whole rule.
2. **Machine-fixable.** Run the fixer. Import order, dead suppressions, obsolete syntax — the diff is large and needs no reading.
3. **The formatter, once, as its own commit.** Add that commit's hash to `.git-blame-ignore-revs`.
4. **What's left is the real backlog — and it must never block a commit.** A checker that reports a file's existing problems every time someone edits one line of it has one outcome: everybody starts passing `--no-verify`, and the checker no longer checks anything. Two mechanisms, depending on what the tool offers:

   - **A baseline file**, when the tool has one (type checkers usually do). Existing errors go in it and stay quiet; anything new is reported from day one. Commit the baseline — it belongs to the branch like the config does. Prefer this over the tool's bulk-suppress command, which writes an ignore comment at every site: thousands of lines of source noise to say nothing.
   - **Filter to the changed lines**, when it does not. Run the linter with JSON output, intersect its line numbers with `git diff --unified=0`, report only the overlap. Two traps: the linter reports absolute paths while git reports repo-relative ones, so normalise before comparing; and untracked files appear in no diff at all, so pull them in separately and treat every line as new.

   The formatter needs its own answer: it rewrites whole files, so running it on an existing file *is* touching the backlog. Run it on newly added files only.

The point of both is that the checker is **useful on day one** rather than after a cleanup nobody schedules.

## Probe every checker

The failure that costs the most is a checker that silently does nothing: a type-aware linter that never found its engine, a baseline that swallows everything, a rule set that excluded the directory it was aimed at. All three report success.

So write a file that must fail, run the checker on it, confirm it fails, delete it. One probe per checker, each aimed at the mechanism you would otherwise be trusting:

| Checker | Probe |
| --- | --- |
| Type checker with a baseline | A new type error in a new file — the baseline must not cover it |
| Type-aware linter | A floating promise, or anything else undecidable without type information |
| Template linter | An unclosed tag and an image without alt text |
| Formatter | A badly formatted file — `--check` must reject it |

Report each checker's count **and** its probe result. A count alone does not distinguish a clean repository from a checker that never ran.
