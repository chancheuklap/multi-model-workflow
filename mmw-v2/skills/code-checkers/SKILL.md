---
name: code-checkers
description: A repository's linter, formatter and type checker. Use when a repository has none, when a language is added to one that has them, when a checker it uses was superseded (pyright, eslint, tsc --noEmit, black, isort), or when commits should run them through a pre-commit hook.
---

# Code checkers

Give a repository the checkers its languages need, wired so a fresh clone or a new worktree has them at the right version without anyone remembering to install anything.

## The rule that decides where a tool goes

**A tool whose version changes what the repository produces belongs to the repository.** A formatter reflows files; a linter's ruleset decides what passes; a compiler decides what ships. Install those through the project's own dependency manifest, so checking out a branch checks out the checkers that branch was written against.

Everything else — the editor, the agent CLI, `ripgrep`, `docker` — belongs to the machine.

## What to install

| Language | Tool | Manifest | Reference |
| --- | --- | --- | --- |
| Python | `ruff` (lint **and** format) | `[dependency-groups] dev` | [references/python.md](references/python.md) |
| Python types | `pyrefly` | same | [references/python.md](references/python.md) |
| Jinja / Django templates | `djlint` | same | [references/python.md](references/python.md) |
| TypeScript / JavaScript | `oxlint` + `oxlint-tsgolint` | `devDependencies` | [references/typescript.md](references/typescript.md) |
| Shell | `shellcheck`, `shfmt` | machine — no language manifest owns them | — |
| Running them at commit time | `prek` | machine, same reason | [references/git-hooks.md](references/git-hooks.md) |

Settled choices, and the fact that decides each:

- **`pyrefly`, not `pyright`** — pyright needs Node and is an order of magnitude slower on a full check. **Not `ty`** — it has not reached a stable release and fails part of the typing conformance suite; fine as an editor server, not as a gate. Re-check both facts against the tools' own release pages before repeating them to a user.
- **`oxlint`, not `eslint`** — TypeScript 7 ships no stable programmatic API, so `typescript-eslint` cannot run on it. `oxlint-tsgolint` embeds the TS 7 engine itself.
- **No separate `tsc --noEmit`** — `oxlint --type-aware --type-check` shares one TypeScript program between the lint pass and the type pass.
- **`ruff` replaces black, isort, flake8, pyupgrade, bandit** — one binary, and the format and lint passes agree with each other by construction.

## Pin the formatter exactly, the checkers loosely

A formatter's output changes between patch releases. Two branches formatted by two versions produce whole-file diffs that collide on every merge, so pin it to an exact version. A linter's new release only adds diagnostics — it rewrites nothing — so a compatible range is right, and keeps the tool moving.

Pin exactly, too, anything whose version is coupled to another tool's; a range drifts off the tool it has to match.

Upgrading is then one deliberate act: bump, run everything, absorb the changes in one commit.

## Steps

1. **Count the files per language.** A language with a handful of files does not need a checker.
2. **Add each tool to the project manifest** and install (`uv sync`, `pnpm install`). Never globally.
3. **Configure** — per-language detail in the reference files. Configure before looking at the error count: most of a first run is misconfiguration, not debt.
4. **Reduce a first run to real findings.** A first run on an existing codebase reports thousands. Almost none of it is worth a human's attention, and reading it in the order the tool printed it is how the whole effort gets abandoned. Separate it in this order:

   1. **Misconfiguration.** Import roots the checker cannot resolve, dependencies absent by design on this platform, framework idioms the rule was not written for. This is usually most of the count. Fix the config, not the code — and exempt precisely: a framework's specific calls, not the whole rule.
   2. **Machine-fixable.** Run the fixer. Import order, dead suppressions, obsolete syntax — the diff is large and needs no reading.
   3. **The formatter, by one rule.** A repository with no open branches and no tickets in flight gets one commit that reformats every file; add that commit's hash to `.git-blame-ignore-revs`. Any other repository formats newly added files only: reformatting an existing file collides with every open branch that touches it.
   4. **What's left is the real backlog — and it must never block a commit.** A checker that reports a file's existing problems every time someone edits one line of it has one outcome: everybody starts passing `--no-verify`, and the checker no longer checks anything. Two mechanisms, depending on what the tool offers:

      - **A checker baseline**, when the tool has one (type checkers usually do). Existing errors go in it and stay quiet; anything new is reported from day one. Commit the baseline — it belongs to the branch like the config does. Prefer this over the tool's bulk-suppress command, which writes an ignore comment at every site: thousands of lines of source noise to say nothing.
      - **Filter to the changed lines**, when it does not. Run the linter with JSON output, intersect its line numbers with `git diff --unified=0`, report only the overlap. Two traps: the linter reports absolute paths while git reports repository-relative ones, so normalise before comparing; and untracked files appear in no diff at all, so pull them in separately and treat every line as new.
5. **Probe every checker.** A checker that never ran reports the same zero as a clean repository. For each one, write a file that must fail, run the checker on it, confirm it fails, delete it: a new type error in a new file for a type checker with a baseline (the baseline must not cover it); a floating promise, or anything else undecidable without type information, for a type-aware linter; an unclosed tag and an image without alt text for a template linter; a badly formatted file that `--check` rejects for a formatter. Report each checker's count and its probe result.
   Done when every checker reported a planted defect.
6. **Write one entry point** that runs them all, reporting only, with a flag for the fixes that are safe to apply. Keep per-checker output to its summary line; a failing step prints its tail and the command to re-run for the full output.
7. **Run them at commit time** — [references/git-hooks.md](references/git-hooks.md). Wire this even when per-agent automation is out of scope, because it is not per-agent.
   Done when a probe commit was refused as `git-hooks.md` `## Probe it with a real commit` describes.
8. **Record it where the next agent reads** — the repository's `AGENTS.md`: which tools, which manifest installs them, the one command, the commit hook and how to skip it, and that the type checker runs against a checker baseline. The one command goes in as a row of the `## Commands` table and the rest under `## Key Conventions` when the file has those headings (the format the `manage-agents-md` skill keeps); otherwise beside the file's existing commands.
   Done when the repository's `AGENTS.md` names the tools, the one command, the hook and how to skip it.
