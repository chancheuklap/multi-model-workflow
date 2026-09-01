# Running the checkers at commit time

The git hook is the only place every author passes through — a person typing `git commit`, and every coding agent regardless of its own hook format. Agent hook systems have not converged: event names, payload shapes and exit-code meanings differ per vendor, and some have no post-edit event at all. One `pre-commit` hook covers all of them and costs one implementation.

`prek` runs it: a Rust reimplementation of `pre-commit`, single binary, no runtime of its own, and it reads the same `.pre-commit-config.yaml`. Install it at machine scope — no language's package manager owns it. (`lefthook` is the other single-binary option and runs hooks in parallel, but it does not isolate staged content, so it checks files the commit does not contain.)

## Point every hook at the checkers the repo already installed

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff format
        entry: uv run ruff format --force-exclude
        language: system
        types_or: [python, pyi]
```

`language: system` means prek runs the command as-is instead of building an environment of its own. Without it you get a second copy of every checker, on its own version schedule, disagreeing with the manual entry point about whether the code passes.

`--force-exclude` matters whenever a checker is handed explicit filenames: several ignore their own exclude config unless told to apply it to named files.

## Three shapes of hook

| Shape | Config | Example |
| --- | --- | --- |
| Per-file | `types_or:` / `files:`, filenames passed | linters, formatters |
| Whole-project | `pass_filenames: false` | a type checker — it must see the whole project to infer anything |
| Runs in a subdirectory | `env -C <dir>` plus `pass_filenames: false` | a linter that needs its package's config and `node_modules` |

For the third shape, `files:` still decides *whether* the hook fires — scope it to that package's sources so touching an unrelated file does not run it.

## What may rewrite files, and on which files

A formatter in the hook is right in principle — its output is deterministic, it changes layout only, and the commit stops so the author re-stages. But on a repository with a formatting backlog, running it on an **existing** file reflows the whole file: a one-line edit turns into a hundred-line diff of somebody else's code. Scope it to files this commit **adds**; existing files are the backlog's problem, not this commit's.

A fixer that rewrites semantics belongs in neither: it edits logic in a hook nobody is reading, at the moment attention is on the commit message. Report those and let the author look.

## The `core.hooksPath` trap

If the repo sets `core.hooksPath` — Git LFS does this, so does any repo with checked-in hooks — then `.git/hooks/` **is never executed**. `prek install` writes there, reports success, and the hook silently never fires.

Check first:

```bash
git config core.hooksPath
```

If it is set, write the hook yourself into that directory instead of running `prek install`:

```bash
#!/usr/bin/env bash
set -euo pipefail

command -v prek >/dev/null 2>&1 || {
  printf '[hook] prek is not installed; this commit was not checked.\n' >&2
  exit 0
}

exec prek run
```

Whether a missing prek should skip or block is the repo's call: skip where other machines clone the repo without the toolchain, block where every author is expected to have it.

## prek stashes unstaged changes

Before running, prek stashes everything not staged, so the hooks see exactly the tree the commit will create. Correct, and worth knowing while testing: config you have edited but not staged is invisible to the hooks, and a checker will report against the committed version of its own config. A first test that produces a flood of errors is usually this, not the config.

## Probe it with a real commit

Write a file that must fail, stage it, and run `git commit` for real. Confirm four things:

1. The commit was refused — `git log` is unchanged.
2. The checker that should have caught it named the actual defect.
3. The formatter rewrote the file.
4. Checkers for untouched languages report `(no files to check) Skipped`.

Then unstage, delete the probe, and confirm the tree is back where it started. Anything less and you have tested the config file, not the hook.
