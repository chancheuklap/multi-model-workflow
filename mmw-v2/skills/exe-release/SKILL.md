---
name: exe-release
description: Build an official install package from the code on the current branch. Use when the user asks to ship, to package, or to build an installer, or when the work touched a product that has a release key.
---

# Release

Ship an install package for every product this change touched, far enough that the user can install it.

**Ship what is on the current branch now.** Whether the code is reviewed, whether it is finished, whether it is a good idea — that is the user's call, already made when they asked. Do not re-judge it here.

## Resolve `<release>` once

`<release>` in every command below is `bash <absolute path of scripts/release-flow.sh>` — the engine, next to this file — so `<release> where` runs `bash /…/scripts/release-flow.sh where`. `<release-scripts>` is the `scripts/` directory that engine lives in, and [key.md](references/key.md) runs two more executables out of it. Resolve both from this file's own location, once. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from.

The engine is the deterministic layer: the state machine, the three failure grades, path guards, same-cause circuit breakers, and budget breakers all live there. **You are the judgment layer:** name the products for this run, read the state and run the action it names, and diagnose the one class of pause the engine cannot judge. Grades, guards, and the executor stay with the engine — [driving.md](references/driving.md) states that boundary at the step where it applies.

## Exit codes

The engine puts *what happened* on stdout — `STAGE:`, `PAUSED:`, `SUCCESS:`, `DONE`, `NOT-DONE:`, `CORRUPT:`, `TRANSIENT-RETRY:`, `ENV-ACTION:`, `P0:`, `BUDGET-EXCEEDED:` and the rest. The exit code says only which of three things happened. The three are the same for every subcommand.

| Command | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| `<release> <subcommand>` | the subcommand ran; what happened is on stdout | one `ERROR: <the fact it cannot get past>` line on stderr | the subcommand is missing or not recognised, usage on stderr (`--help` exits 0) | — |
| `<release-scripts>/verify_key.py` | no findings | findings, JSON envelope on stdout | argparse usage error | — |
| `<release-scripts>/release_script_assembler.py assemble\|check` | passed | — | argparse usage error | `INVALID: <reason>` on stderr |

**`PAUSED` exits 0.** So do `CORRUPT:`, `BUDGET-EXCEEDED:` and every other verdict: they are things that happened, and a subcommand that reaches a verdict ran. Read the state from stdout, never from the exit code.

Exit 1 is the engine refusing to go on because of a fact — a `budget.started_at` that will not parse, no release-state where a subcommand needs one. The `ERROR:` line names that fact.

## 1. Preconditions

Both must hold. If one fails, stop and name it.

| Check | How |
| --- | --- |
| Working tree is clean | `git status --porcelain` is empty. The engine refuses to mix self-heal commits with uncommitted work |
| This repo ships something | At least one release key exists (next step) |

**A repo with no release key at all does not ship.** Report that, and the current branch HEAD. Hand back to the user. (One product missing a release key in a repo that does ship is a different case — step 2.)

## 2. Name the products for this run

The repo registers release keys. One product per file. The filename ends with `.release-adapter.json`. List them:

```bash
grep -rl '"product"' --include='*.release-adapter.json' .
```

Decide which to ship: take the paths this change touched (`git diff --name-only $(git merge-base HEAD <parent>)..HEAD`; `<parent>` is the branch this task branch was created from — the repo default branch when you have nothing better). Match them against the paths each config names — its shell directory, its compile entrypoints and packaged data, its `asset_roots`. A hit means ship that product.

If you cannot tell, include the product and write the reason in the table below, then continue. Do not omit a product. A product whose config names no path that could ever match is a config to fix, not a product to skip.

**A product this change touched but no release key names does not ship yet.** Bringing it in is one
JSON file plus whatever the repo still lacks: [new-product.md](references/new-product.md) starts there and
hands off to [key.md](references/key.md) for the fields. Do not write packaging scripts in the product repo
to work around a release key that cannot say something; add the field or the capability, where every
product gets it.

Show this list once and continue. Do not wait for a reply:

```
| product | release key | why this run includes it |
```

## 3. One product per loop, driven by driving.md

For each product from step 2, in order:

```bash
<release> init --manifest <absolute path of that config>
```

Then read [driving.md](references/driving.md) in full and drive until the package is ready. **That file is the driving contract.** This skill does not retell it.

`<release> close` one product before starting the next. Do not run two at once — the repo has one state file.

A round that will not produce a package — the product is blocked and you are shipping another one first — is ended the way [driving.md](references/driving.md)'s **Close** section says. It matters at this level because step 4 below reads delivery records as fact.

## 4. Same-commit check

Do this after every product has shipped. A stage, a dispatch, or a self-heal can create new commits, so an earlier package may not match the final code.

```bash
git rev-parse HEAD
```

Delivery records live under `.release/delivered/`, at the **main checkout root**, not in this task worktree.

That directory holds one record per product. A later run overwrites the earlier one. **Read only the products on the step 2 list.** Their `source_commit` values must all equal current HEAD.

A mismatch: ship that product again (back to step 3, only the mismatches). Then check again — a reship can create new commits.

**Do not give the user a mixed-commit set of packages.**

## 5. User install test

[driving.md](references/driving.md)'s **Close** section says where a package path comes from and what to say when there is none.

Give the user: which products shipped, where each package is, which commit this set is.

**Stop and wait for the user to install and try it.** The machine cannot judge install or use. Pass: report the packages, the commit, and the test result, then hand back to the user. Fail: open a `needs-triage` ticket with the symptoms and repro steps, have it triaged to `ready-for-agent`, then dispatch `implement #<n>`; ship again after it closes.
