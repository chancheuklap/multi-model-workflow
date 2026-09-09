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
| Python | `ruff` (lint **and** format) | `[dependency-groups] dev` | [references/python.md](references/python.md) |
| Python types | `pyrefly` | same | [references/python.md](references/python.md) |
| Jinja / Django templates | `djlint` | same | [references/python.md](references/python.md) |
| TypeScript / JavaScript | `oxlint` + `oxlint-tsgolint` | `devDependencies` | [references/typescript.md](references/typescript.md) |
| Shell | `shellcheck`, `shfmt` | machine — no language manifest owns them | — |
| Running them at commit time | `prek` | machine, same reason | [references/git-hooks.md](references/git-hooks.md) |

Choices worth not relitigating, and the fact that decides each:

- **`pyrefly`, not `pyright`** — pyright needs Node and is an order of magnitude slower on a full check. **Not `ty`** — it has not reached a stable release and fails part of the typing conformance suite; fine as an editor server, not as a gate. Re-check both facts against the tools' own release pages before repeating them to a user.
- **`oxlint`, not `eslint`** — TypeScript 7 ships no stable programmatic API, so `typescript-eslint` cannot run on it. `oxlint-tsgolint` embeds the TS 7 engine itself.
- **No separate `tsc --noEmit`** — `oxlint --type-aware --type-check` shares one TypeScript program between the lint pass and the type pass.
- **`ruff` replaces black, isort, flake8, pyupgrade, bandit** — one binary, and the format and lint passes agree with each other by construction.

## Pin the formatter exactly, the checkers loosely

A formatter's output changes between patch releases. Two branches formatted by two versions produce whole-file diffs that collide on every merge, so pin it to an exact version. A linter's new release only adds diagnostics — it rewrites nothing — so a compatible range is right, and keeps the tool moving.

Pin exactly, too, anything whose version is coupled to another tool's; a range drifts off the tool it has to match.

Upgrading is then one deliberate act — bump, run everything, absorb the changes in one commit — instead of a failure on a day nobody planned for.

## Steps

1. **Count the files per language.** Install only for languages that need it.
2. **Add each tool to the project manifest** and install (`uv sync`, `pnpm install`). Never globally.
3. **Configure** — per-language detail in the reference files. Configure before looking at the error count: most of a first run is misconfiguration, not debt.
4. **Take a first run down to signal** — [references/first-run.md](references/first-run.md).
5. **Probe every checker** — [references/probing.md](references/probing.md). A checker that reports zero because it never ran is worse than none.
6. **Write one entry point** that runs them all, reporting only, with a flag for the fixes that are safe to apply. Keep per-checker output to its summary line; a failing step prints its tail and the command to rerun for the full output.
7. **Run them at commit time** — [references/git-hooks.md](references/git-hooks.md). Wire this even when per-agent automation is out of scope, because it is not per-agent.
8. **Record it where the next agent reads** — the repo's `AGENTS.md`: which tools, which manifest installs them, the one command, the commit hook and how to skip it, and that the type checker runs against a checker baseline.
